"""
Core bulk operation logic.

Provides operation classes for:
- Bulk create
- Bulk update
- Bulk upsert
- Bulk delete

Pure Django ORM, no DRF dependencies.
"""

from .results import BulkOperationResult
from .queries import BulkQueryBuilder
from .utils import BatchProcessor, M2MHandler, build_unique_key, normalize_unique_fields
from .exceptions import ObjectNotFoundError
from .monitoring import get_monitor
from .settings import bulk_settings


class BulkOperation:
    """
    Abstract base for all bulk operations.
    Encapsulates common setup and result handling.
    """

    def __init__(self, model, unique_fields=None, batch_size=None, context=None):
        """
        Initialize operation with configuration.

        Args:
            model: Django model class
            unique_fields: List of fields for matching (upsert/update)
            batch_size: Records per batch
            context: Additional context (user, request, etc.)
        """
        self.model = model
        # Store raw unique fields (without _id suffix) for native upsert
        self.raw_unique_fields = unique_fields or ["id"]
        # Normalize unique_fields to handle FK fields (convert to _id suffix)
        self.unique_fields = normalize_unique_fields(model, self.raw_unique_fields)
        self.batch_size = batch_size or bulk_settings.default_batch_size
        self.context = context or {}

        self.result = BulkOperationResult()
        self.query_builder = BulkQueryBuilder(model, self.unique_fields)
        self.batch_processor = BatchProcessor(self.batch_size)
        self.m2m_handler = M2MHandler(model)

        # Get monitor from settings
        self.monitor = get_monitor()

    def execute(self, validated_data, m2m_data=None):
        """
        Execute the operation.
        Must be implemented by subclasses.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional M2M data list

        Returns:
            BulkOperationResult
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def get_result(self):
        """
        Get operation result object.

        Returns:
            BulkOperationResult instance
        """
        return self.result
    
    def _resolve_foreign_keys(self, validated_data):
        """
        Convert foreign key IDs to model instances efficiently.
        
        For fields that are ForeignKey relations, if the validated_data contains
        integer IDs (from PrimaryKeyRelatedField), we need to convert them to
        actual model instances before creating/updating Django model objects.
        
        This method does this in a single query per FK field (no N+1 queries).
        
        Also refreshes any FK instances that are "lazy" (not fully loaded) to prevent
        N+1 queries when accessing their attributes during bulk operations.
        
        Args:
            validated_data: List of validated data dicts
            
        Returns:
            List of validated data dicts with FK IDs replaced by instances
        """
        from django.db.models import Model
        
        if not validated_data:
            return validated_data
        
        # Identify foreign key fields in the model
        fk_fields = {}
        for field in self.model._meta.get_fields():
            if field.many_to_one and field.concrete:  # ForeignKey
                fk_fields[field.name] = field
        
        if not fk_fields:
            # No foreign keys to resolve
            return validated_data
        
        # Collect all FK IDs that need to be fetched (grouped by field)
        # This includes both integer IDs AND PKs from existing model instances
        fk_ids_to_fetch = {field_name: set() for field_name in fk_fields.keys()}
        
        for data in validated_data:
            for field_name, field in fk_fields.items():
                if field_name in data:
                    value = data[field_name]
                    # Check if it's an integer ID
                    if isinstance(value, int):
                        fk_ids_to_fetch[field_name].add(value)
                    # Check if it's a model instance (might be lazy-loaded)
                    elif isinstance(value, Model):
                        # Collect PK to re-fetch and avoid lazy loading
                        fk_ids_to_fetch[field_name].add(value.pk)
        
        # Fetch all FK instances in a single query per field
        fk_instances = {}
        for field_name, ids in fk_ids_to_fetch.items():
            if ids:
                field = fk_fields[field_name]
                related_model = field.related_model
                # Single query to fetch all instances for this FK field
                instances = related_model.objects.filter(pk__in=ids)
                fk_instances[field_name] = {instance.pk: instance for instance in instances}
        
        # Replace integer IDs and lazy instances with fully-loaded instances in validated_data
        resolved_data = []
        for data in validated_data:
            resolved_item = data.copy()
            for field_name, field in fk_fields.items():
                if field_name in resolved_item:
                    value = resolved_item[field_name]
                    # Replace integer ID with instance
                    if isinstance(value, int) and field_name in fk_instances:
                        instance = fk_instances[field_name].get(value)
                        if instance is not None:
                            resolved_item[field_name] = instance
                        # If instance not found, leave the ID as-is and let Django raise error
                    # Replace lazy model instance with fully-loaded instance
                    elif isinstance(value, Model) and field_name in fk_instances:
                        instance = fk_instances[field_name].get(value.pk)
                        if instance is not None:
                            resolved_item[field_name] = instance
            resolved_data.append(resolved_item)
        
        return resolved_data


class BulkCreateOperation(BulkOperation):
    """
    Bulk create operation using Model.objects.bulk_create().
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk create.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("create", len(validated_data)):
            # Prepare instances
            instances = self._prepare_instances(validated_data)

            # Batch create
            created_instances = self._batch_create(instances)

            # Set M2M relations if provided
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(created_instances, m2m_data)

            # Add to result
            for instance in created_instances:
                self.result.add_created(instance)


        return self.result

    def _prepare_instances(self, validated_data):
        """
        Convert validated dicts to unsaved model instances.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of unsaved model instances
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        instances = []
        for data in resolved_data:
            instance = self.model(**data)
            instances.append(instance)
        return instances

    def _batch_create(self, instances):
        """
        Execute bulk_create in batches.

        Args:
            instances: List of model instances

        Returns:
            List of created instances with IDs
        """
        all_created = []

        for batch in self.batch_processor.chunk_list(instances):
            created = self.model.objects.bulk_create(batch, batch_size=self.batch_size)
            all_created.extend(created)

        return all_created


class BulkUpdateOperation(BulkOperation):
    """
    Bulk update operation using Model.objects.bulk_update().
    Requires all objects to exist.
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk update.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("update", len(validated_data)):
            # Fetch existing objects
            existing = self._fetch_existing(validated_data)

            # Validate all exist
            self._validate_all_exist(validated_data, existing)

            # Apply updates
            instances, update_fields = self._apply_updates(existing, validated_data)

            # Batch update
            self._batch_update(instances, update_fields)

            # Set M2M relations if provided
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(instances, m2m_data)

            # Add to result
            for instance in instances:
                self.result.add_updated(instance)

        return self.result

    def _fetch_existing(self, validated_data):
        """
        Single query to fetch all existing objects.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Dict mapping unique_key → instance
        """
        queryset = self.model.objects.all()
        return self.query_builder.fetch_by_unique_fields(queryset, validated_data)

    def _validate_all_exist(self, validated_data, existing):
        """
        Ensure all items in validated_data match existing objects.

        Args:
            validated_data: List of validated data dicts
            existing: Dict of existing instances by unique key

        Raises:
            ObjectNotFoundError: If any objects missing
        """
        missing_keys = []

        for data in validated_data:
            key = build_unique_key(data, self.unique_fields)
            if key not in existing:
                missing_keys.append(dict(zip(self.unique_fields, key)))

        if missing_keys:
            raise ObjectNotFoundError(missing_keys)

    def _apply_updates(self, existing, validated_data):
        """
        Apply validated_data updates to existing instances.

        Args:
            existing: Dict of existing instances by unique key
            validated_data: List of validated data dicts

        Returns:
            Tuple of (instances, update_fields)
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        instances = []
        all_fields = set()

        for data in resolved_data:
            key = build_unique_key(data, self.unique_fields)
            instance = existing[key]

            # Apply updates
            for field, value in data.items():
                if field not in self.unique_fields:  # Don't update unique fields
                    setattr(instance, field, value)
                    all_fields.add(field)

            instances.append(instance)

        # Return union of all fields being updated
        update_fields = list(all_fields)
        return instances, update_fields

    def _batch_update(self, instances, update_fields):
        """
        Execute bulk_update in batches.

        Args:
            instances: List of instances to update
            update_fields: List of fields to update
        """
        if not update_fields:
            return

        for batch in self.batch_processor.chunk_list(instances):
            self.model.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)


class BulkUpsertOperation(BulkOperation):
    """
    Bulk upsert (create or update) operation using Django's native bulk_create with update_conflicts.
    
    This provides maximum performance with a single database operation.
    Requires Django 4.1+ and compatible database (PostgreSQL, SQLite 3.24+, MySQL 8.0.19+).
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute native upsert using Django's bulk_create with update_conflicts.
        Single database operation - much faster than traditional SELECT + CREATE/UPDATE approach.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("upsert", len(validated_data)):
            # Determine update fields (all non-unique fields)
            update_fields = self._get_update_fields(validated_data)

            # Prepare instances
            instances = self._prepare_instances(validated_data)

            # Execute native upsert - single database operation!
            upserted_instances = self._native_batch_upsert(instances, update_fields)

            # Handle M2M relationships
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(upserted_instances, m2m_data)

            # Add to result (native upsert doesn't distinguish created vs updated)
            for instance in upserted_instances:
                self.result.add_created(instance)


        return self.result

    def _prepare_instances(self, validated_data):
        """
        Convert validated dicts to unsaved model instances for native upsert.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of unsaved model instances
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        return [self.model(**data) for data in resolved_data]

    def _get_update_fields(self, validated_data):
        """
        Determine which fields should be updated on conflict for native upsert.
        Returns all non-unique fields that appear in the validated data.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of field names to update on conflict
        """
        all_fields = set()
        for data in validated_data:
            all_fields.update(data.keys())
        
        # Exclude unique fields from updates (they're used for matching, not updating)
        return [f for f in all_fields if f not in self.raw_unique_fields]

    def _native_batch_upsert(self, instances, update_fields):
        """
        Execute native upsert using Django's bulk_create with update_conflicts.
        Single database operation that handles both creates and updates.
        
        Requires Django 4.1+ and compatible database backend.

        Args:
            instances: List of model instances to upsert
            update_fields: List of fields to update on conflict

        Returns:
            List of upserted instances
        
        Raises:
            NotImplementedError: If Django < 4.1 or database doesn't support native upsert
        """
        all_upserted = []

        try:
            for batch in self.batch_processor.chunk_list(instances):
                upserted = self.model.objects.bulk_create(
                    batch,
                    update_conflicts=True,
                    update_fields=update_fields,
                    unique_fields=self.raw_unique_fields,  # Use field names, not DB column names
                    batch_size=self.batch_size
                )
                all_upserted.extend(upserted)
        except (TypeError, NotImplementedError) as e:
            # TypeError: Django < 4.1 doesn't recognize update_conflicts parameter
            # NotImplementedError: Database backend doesn't support this feature
            raise NotImplementedError(
                f"Native upsert requires Django 4.1+ and a compatible database backend. "
                f"Supported databases: PostgreSQL, SQLite 3.24+, MySQL 8.0.19+. "
                f"Error: {str(e)}"
            ) from e

        return all_upserted


class BulkDeleteOperation(BulkOperation):
    """
    Bulk delete operation using QuerySet.delete().
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk delete.

        Args:
            validated_data: List of validated data dicts with unique field values
            m2m_data: Not used for delete operations

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("delete", len(validated_data)):
            # Build queryset
            queryset = self._build_queryset(validated_data)

            # Execute delete
            count = self._batch_delete(queryset)

            # Set result
            self.result.set_deleted_count(count)

        return self.result

    def _build_queryset(self, validated_data):
        """
        Build queryset matching unique_fields in validated_data.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Filtered queryset
        """
        q_filter = self.query_builder.build_lookup_filter(validated_data)
        return self.model.objects.filter(q_filter)

    def _batch_delete(self, queryset):
        """
        Execute delete.

        Args:
            queryset: Queryset to delete

        Returns:
            Total deleted count
        """
        deleted_count, _ = queryset.delete()
        return deleted_count
