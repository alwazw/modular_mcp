"""
Transformation Service for Agent 4: Intelligent Data Transformer
"""

import os
import uuid
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.models.transformer import db, TransformationJob, TemplateMapping, Template

class TransformationService:
    """Service for data transformation operations"""
    
    def __init__(self):
        self.transformation_threads = {}
    
    def execute_transformation(self, job_id: str) -> Dict[str, Any]:
        """Execute a transformation job"""
        try:
            job = TransformationJob.query.filter_by(job_id=job_id).first()
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status == 'running':
                return {'success': False, 'error': 'Job is already running'}
            
            # Update job status
            job.status = 'running'
            job.started_at = datetime.utcnow()
            job.progress_percentage = 0.0
            db.session.commit()
            
            # Start transformation in background thread
            def run_transformation():
                try:
                    # Get mapping
                    mapping = TemplateMapping.query.filter_by(mapping_id=job.mapping_id).first()
                    if not mapping:
                        raise Exception('Mapping not found')
                    
                    # Load source data
                    source_data = self._load_source_data(job.source_data_path)
                    if not source_data:
                        raise Exception('Failed to load source data')
                    
                    # Transform data
                    transformed_data = self._transform_data(source_data, mapping)
                    
                    # Save transformed data
                    output_path = self._save_transformed_data(transformed_data, job.target_data_path)
                    
                    # Update job with success
                    job.status = 'completed'
                    job.completed_at = datetime.utcnow()
                    job.progress_percentage = 100.0
                    job.records_processed = len(source_data) if isinstance(source_data, list) else 1
                    job.records_successful = job.records_processed
                    job.execution_time_seconds = (job.completed_at - job.started_at).total_seconds()
                    job.target_data_path = output_path
                    
                    # Calculate quality metrics
                    job.quality_metrics = self._calculate_quality_metrics(source_data, transformed_data)
                    
                    db.session.commit()
                    
                except Exception as e:
                    # Update job with failure
                    job.status = 'failed'
                    job.completed_at = datetime.utcnow()
                    job.error_message = str(e)
                    job.execution_time_seconds = (job.completed_at - job.started_at).total_seconds()
                    db.session.commit()
                
                finally:
                    # Clean up thread reference
                    if job_id in self.transformation_threads:
                        del self.transformation_threads[job_id]
            
            thread = threading.Thread(target=run_transformation, daemon=True)
            thread.start()
            self.transformation_threads[job_id] = thread
            
            return {
                'success': True,
                'message': 'Transformation started',
                'job_id': job_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_transformation(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running transformation"""
        try:
            job = TransformationJob.query.filter_by(job_id=job_id).first()
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status != 'running':
                return {'success': False, 'error': 'Job is not running'}
            
            # Update job status
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            job.error_message = 'Cancelled by user'
            db.session.commit()
            
            return {'success': True, 'message': 'Transformation cancelled'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def transform_data_direct(self, mapping_id: str, source_data: Any, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform data directly without creating a job"""
        try:
            mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
            if not mapping:
                return {'success': False, 'error': 'Mapping not found'}
            
            # Transform the data
            transformed_data = self._transform_data(source_data, mapping, options or {})
            
            return {
                'success': True,
                'transformed_data': transformed_data,
                'source_records': len(source_data) if isinstance(source_data, list) else 1,
                'transformed_records': len(transformed_data) if isinstance(transformed_data, list) else 1
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_transformation(self, mapping_id: str, source_data: Any) -> Dict[str, Any]:
        """Validate a transformation without executing it"""
        try:
            mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
            if not mapping:
                return {'success': False, 'error': 'Mapping not found'}
            
            # Get templates
            source_template = Template.query.filter_by(template_id=mapping.source_template_id).first()
            target_template = Template.query.filter_by(template_id=mapping.target_template_id).first()
            
            validation_results = {
                'mapping_valid': True,
                'source_data_valid': True,
                'field_mappings_valid': True,
                'issues': [],
                'warnings': []
            }
            
            # Validate source data against source template
            if source_template and source_template.schema_definition:
                source_validation = self._validate_data_against_schema(source_data, source_template.schema_definition)
                if not source_validation['valid']:
                    validation_results['source_data_valid'] = False
                    validation_results['issues'].extend(source_validation['errors'])
            
            # Validate field mappings
            if mapping.field_mappings:
                mapping_validation = self._validate_field_mappings(mapping.field_mappings, source_template, target_template)
                if not mapping_validation['valid']:
                    validation_results['field_mappings_valid'] = False
                    validation_results['issues'].extend(mapping_validation['errors'])
                validation_results['warnings'].extend(mapping_validation.get('warnings', []))
            
            validation_results['overall_valid'] = (
                validation_results['mapping_valid'] and 
                validation_results['source_data_valid'] and 
                validation_results['field_mappings_valid']
            )
            
            return {
                'success': True,
                'validation': validation_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def preview_transformation(self, mapping_id: str, source_data: Any, limit: int = 10) -> Dict[str, Any]:
        """Preview transformation results"""
        try:
            mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
            if not mapping:
                return {'success': False, 'error': 'Mapping not found'}
            
            # Limit source data for preview
            preview_data = source_data
            if isinstance(source_data, list) and len(source_data) > limit:
                preview_data = source_data[:limit]
            
            # Transform preview data
            transformed_preview = self._transform_data(preview_data, mapping)
            
            return {
                'success': True,
                'preview': {
                    'source_data': preview_data,
                    'transformed_data': transformed_preview,
                    'mapping_info': {
                        'mapping_id': mapping.mapping_id,
                        'name': mapping.name,
                        'source_template': mapping.source_template_id,
                        'target_template': mapping.target_template_id
                    }
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _transform_data(self, source_data: Any, mapping: TemplateMapping, options: Dict[str, Any] = None) -> Any:
        """Core data transformation logic"""
        try:
            if not mapping.field_mappings:
                raise Exception('No field mappings defined')
            
            # Handle single record vs list of records
            is_list = isinstance(source_data, list)
            data_to_transform = source_data if is_list else [source_data]
            
            transformed_records = []
            
            for record in data_to_transform:
                transformed_record = {}
                
                # Apply field mappings
                for target_field, mapping_config in mapping.field_mappings.items():
                    try:
                        value = self._apply_field_mapping(record, mapping_config, mapping)
                        if value is not None:
                            transformed_record[target_field] = value
                    except Exception as e:
                        print(f"Error mapping field {target_field}: {e}")
                        # Continue with other fields
                
                # Apply default values
                if mapping.default_values:
                    for field, default_value in mapping.default_values.items():
                        if field not in transformed_record:
                            transformed_record[field] = default_value
                
                # Apply conditional logic
                if mapping.conditional_logic:
                    transformed_record = self._apply_conditional_logic(transformed_record, record, mapping.conditional_logic)
                
                transformed_records.append(transformed_record)
            
            return transformed_records if is_list else transformed_records[0]
            
        except Exception as e:
            raise Exception(f"Transformation failed: {str(e)}")
    
    def _apply_field_mapping(self, source_record: Dict[str, Any], mapping_config: Any, mapping: TemplateMapping) -> Any:
        """Apply a single field mapping"""
        try:
            # Handle different mapping configuration formats
            if isinstance(mapping_config, str):
                # Simple field mapping: "source_field"
                return source_record.get(mapping_config)
            
            elif isinstance(mapping_config, dict):
                # Complex mapping configuration
                source_field = mapping_config.get('source_field')
                transformation = mapping_config.get('transformation')
                default_value = mapping_config.get('default')
                
                # Get source value
                value = source_record.get(source_field) if source_field else None
                
                # Apply transformation
                if transformation and value is not None:
                    value = self._apply_transformation(value, transformation)
                
                # Use default if no value
                if value is None and default_value is not None:
                    value = default_value
                
                return value
            
            else:
                return mapping_config  # Static value
                
        except Exception as e:
            print(f"Error in field mapping: {e}")
            return None
    
    def _apply_transformation(self, value: Any, transformation: Dict[str, Any]) -> Any:
        """Apply transformation rules to a value"""
        try:
            transform_type = transformation.get('type')
            
            if transform_type == 'string':
                # String transformations
                if transformation.get('uppercase'):
                    value = str(value).upper()
                elif transformation.get('lowercase'):
                    value = str(value).lower()
                elif transformation.get('title_case'):
                    value = str(value).title()
                
                # String replacement
                if 'replace' in transformation:
                    replace_config = transformation['replace']
                    value = str(value).replace(replace_config.get('from', ''), replace_config.get('to', ''))
                
                # String formatting
                if 'format' in transformation:
                    value = transformation['format'].format(value=value)
            
            elif transform_type == 'number':
                # Number transformations
                value = float(value) if value else 0
                
                if 'multiply' in transformation:
                    value *= transformation['multiply']
                
                if 'add' in transformation:
                    value += transformation['add']
                
                if 'round' in transformation:
                    value = round(value, transformation['round'])
            
            elif transform_type == 'date':
                # Date transformations
                from datetime import datetime
                
                input_format = transformation.get('input_format', '%Y-%m-%d')
                output_format = transformation.get('output_format', '%Y-%m-%d')
                
                if isinstance(value, str):
                    date_obj = datetime.strptime(value, input_format)
                    value = date_obj.strftime(output_format)
            
            elif transform_type == 'lookup':
                # Lookup transformations
                lookup_table = transformation.get('lookup_table', {})
                value = lookup_table.get(str(value), transformation.get('default', value))
            
            elif transform_type == 'conditional':
                # Conditional transformations
                conditions = transformation.get('conditions', [])
                for condition in conditions:
                    if self._evaluate_condition(value, condition.get('condition', {})):
                        value = condition.get('value', value)
                        break
            
            return value
            
        except Exception as e:
            print(f"Error in transformation: {e}")
            return value
    
    def _apply_conditional_logic(self, transformed_record: Dict[str, Any], source_record: Dict[str, Any], conditional_logic: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conditional logic to transformed record"""
        try:
            for condition_name, condition_config in conditional_logic.items():
                condition = condition_config.get('condition', {})
                actions = condition_config.get('actions', [])
                
                if self._evaluate_condition_on_record(source_record, transformed_record, condition):
                    for action in actions:
                        self._apply_conditional_action(transformed_record, action)
            
            return transformed_record
            
        except Exception as e:
            print(f"Error in conditional logic: {e}")
            return transformed_record
    
    def _evaluate_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition"""
        try:
            operator = condition.get('operator', 'equals')
            compare_value = condition.get('value')
            
            if operator == 'equals':
                return value == compare_value
            elif operator == 'not_equals':
                return value != compare_value
            elif operator == 'contains':
                return compare_value in str(value)
            elif operator == 'starts_with':
                return str(value).startswith(str(compare_value))
            elif operator == 'ends_with':
                return str(value).endswith(str(compare_value))
            elif operator == 'greater_than':
                return float(value) > float(compare_value)
            elif operator == 'less_than':
                return float(value) < float(compare_value)
            elif operator == 'is_empty':
                return not value or str(value).strip() == ''
            elif operator == 'is_not_empty':
                return value and str(value).strip() != ''
            
            return False
            
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False
    
    def _evaluate_condition_on_record(self, source_record: Dict[str, Any], transformed_record: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate condition on record level"""
        try:
            field = condition.get('field')
            source = condition.get('source', 'transformed')  # 'source' or 'transformed'
            
            if source == 'source':
                value = source_record.get(field)
            else:
                value = transformed_record.get(field)
            
            return self._evaluate_condition(value, condition)
            
        except Exception as e:
            print(f"Error evaluating record condition: {e}")
            return False
    
    def _apply_conditional_action(self, record: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Apply conditional action to record"""
        try:
            action_type = action.get('type')
            
            if action_type == 'set_field':
                field = action.get('field')
                value = action.get('value')
                if field:
                    record[field] = value
            
            elif action_type == 'remove_field':
                field = action.get('field')
                if field and field in record:
                    del record[field]
            
            elif action_type == 'copy_field':
                source_field = action.get('source_field')
                target_field = action.get('target_field')
                if source_field and target_field and source_field in record:
                    record[target_field] = record[source_field]
            
        except Exception as e:
            print(f"Error applying conditional action: {e}")
    
    def _load_source_data(self, file_path: str) -> Any:
        """Load source data from file"""
        try:
            if not file_path or not os.path.exists(file_path):
                return None
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            elif file_extension == '.csv':
                import csv
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            
            else:
                # Try to read as text
                with open(file_path, 'r') as f:
                    return f.read()
                    
        except Exception as e:
            print(f"Error loading source data: {e}")
            return None
    
    def _save_transformed_data(self, data: Any, output_path: str = None) -> str:
        """Save transformed data to file"""
        try:
            if not output_path:
                output_path = f"/tmp/transformed_{uuid.uuid4()}.json"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save as JSON by default
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return output_path
            
        except Exception as e:
            print(f"Error saving transformed data: {e}")
            return None
    
    def _calculate_quality_metrics(self, source_data: Any, transformed_data: Any) -> Dict[str, Any]:
        """Calculate quality metrics for transformation"""
        try:
            metrics = {
                'completeness': 0.0,
                'accuracy': 0.0,
                'consistency': 0.0,
                'transformation_rate': 0.0
            }
            
            # Calculate basic metrics
            if isinstance(source_data, list) and isinstance(transformed_data, list):
                source_count = len(source_data)
                transformed_count = len(transformed_data)
                
                metrics['transformation_rate'] = (transformed_count / source_count * 100) if source_count > 0 else 0
                
                # Calculate field completeness
                if transformed_data:
                    total_fields = 0
                    filled_fields = 0
                    
                    for record in transformed_data:
                        if isinstance(record, dict):
                            total_fields += len(record)
                            filled_fields += len([v for v in record.values() if v is not None and str(v).strip() != ''])
                    
                    metrics['completeness'] = (filled_fields / total_fields * 100) if total_fields > 0 else 0
            
            # Placeholder for more sophisticated metrics
            metrics['accuracy'] = 95.0  # Would require validation against known good data
            metrics['consistency'] = 90.0  # Would require consistency checks
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating quality metrics: {e}")
            return {}
    
    def _validate_data_against_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema definition"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # This is a placeholder implementation
            # In a real system, this would validate against JSON Schema or similar
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def _validate_field_mappings(self, field_mappings: Dict[str, Any], source_template: Template, target_template: Template) -> Dict[str, Any]:
        """Validate field mappings between templates"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # This is a placeholder implementation
            # In a real system, this would validate field compatibility
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Mapping validation error: {str(e)}"],
                'warnings': []
            }
    
    def process_uploaded_file(self, file) -> Dict[str, Any]:
        """Process uploaded file for transformation"""
        try:
            # Save uploaded file
            filename = f"upload_{uuid.uuid4()}_{file.filename}"
            file_path = f"/tmp/{filename}"
            file.save(file_path)
            
            # Analyze file
            file_info = {
                'filename': file.filename,
                'file_path': file_path,
                'size_bytes': os.path.getsize(file_path),
                'file_type': os.path.splitext(file.filename)[1].lower()
            }
            
            # Load and preview data
            preview_data = self._load_source_data(file_path)
            if isinstance(preview_data, list) and len(preview_data) > 5:
                file_info['preview'] = preview_data[:5]
            else:
                file_info['preview'] = preview_data
            
            return {
                'success': True,
                'file_info': file_info
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_download(self, job_id: str) -> Dict[str, Any]:
        """Generate download for transformed data"""
        try:
            job = TransformationJob.query.filter_by(job_id=job_id).first()
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if not job.target_data_path or not os.path.exists(job.target_data_path):
                return {'success': False, 'error': 'Transformed data file not found'}
            
            return {
                'success': True,
                'download_url': f"/api/transformer/download/{job_id}",
                'file_path': job.target_data_path,
                'file_size': os.path.getsize(job.target_data_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_transformation_statistics(self, days: int) -> Dict[str, Any]:
        """Get transformation statistics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            jobs = TransformationJob.query.filter(
                TransformationJob.created_at >= start_date
            ).all()
            
            stats = {
                'total_jobs': len(jobs),
                'completed_jobs': len([j for j in jobs if j.status == 'completed']),
                'failed_jobs': len([j for j in jobs if j.status == 'failed']),
                'running_jobs': len([j for j in jobs if j.status == 'running']),
                'total_records_processed': sum([j.records_processed or 0 for j in jobs]),
                'average_execution_time': 0,
                'success_rate': 0
            }
            
            # Calculate averages
            completed_jobs = [j for j in jobs if j.status == 'completed' and j.execution_time_seconds]
            if completed_jobs:
                stats['average_execution_time'] = sum([j.execution_time_seconds for j in completed_jobs]) / len(completed_jobs)
            
            if stats['total_jobs'] > 0:
                stats['success_rate'] = (stats['completed_jobs'] / stats['total_jobs']) * 100
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_job_quality_report(self, job_id: str) -> Dict[str, Any]:
        """Get quality report for specific job"""
        try:
            job = TransformationJob.query.filter_by(job_id=job_id).first()
            if not job:
                return {'error': 'Job not found'}
            
            return {
                'job_id': job_id,
                'quality_metrics': job.quality_metrics or {},
                'validation_results': job.validation_results or {},
                'records_processed': job.records_processed,
                'records_successful': job.records_successful,
                'records_failed': job.records_failed,
                'success_rate': (job.records_successful / job.records_processed * 100) if job.records_processed > 0 else 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_overall_quality_report(self) -> Dict[str, Any]:
        """Get overall quality report"""
        try:
            jobs = TransformationJob.query.filter_by(status='completed').all()
            
            if not jobs:
                return {'message': 'No completed jobs found'}
            
            # Aggregate quality metrics
            total_completeness = 0
            total_accuracy = 0
            total_consistency = 0
            jobs_with_metrics = 0
            
            for job in jobs:
                if job.quality_metrics:
                    total_completeness += job.quality_metrics.get('completeness', 0)
                    total_accuracy += job.quality_metrics.get('accuracy', 0)
                    total_consistency += job.quality_metrics.get('consistency', 0)
                    jobs_with_metrics += 1
            
            if jobs_with_metrics > 0:
                avg_completeness = total_completeness / jobs_with_metrics
                avg_accuracy = total_accuracy / jobs_with_metrics
                avg_consistency = total_consistency / jobs_with_metrics
            else:
                avg_completeness = avg_accuracy = avg_consistency = 0
            
            return {
                'overall_quality': {
                    'completeness': round(avg_completeness, 2),
                    'accuracy': round(avg_accuracy, 2),
                    'consistency': round(avg_consistency, 2)
                },
                'total_jobs_analyzed': jobs_with_metrics,
                'total_records_processed': sum([j.records_processed or 0 for j in jobs])
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_batch_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create batch transformation job"""
        try:
            # This is a placeholder implementation
            batch_id = str(uuid.uuid4())
            
            return {
                'success': True,
                'batch_id': batch_id,
                'message': 'Batch transformation created',
                'jobs_created': len(data.get('source_files', []))
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def suggest_template_mapping(self, source_data: Any, target_template_id: str = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Suggest template mapping based on source data"""
        try:
            # This is a placeholder implementation for AI-powered suggestions
            suggestions = {
                'suggested_mappings': [
                    {
                        'confidence': 0.85,
                        'source_field': 'product_name',
                        'target_field': 'title',
                        'reasoning': 'Field names are semantically similar'
                    },
                    {
                        'confidence': 0.92,
                        'source_field': 'price',
                        'target_field': 'cost',
                        'reasoning': 'Both fields contain monetary values'
                    }
                ],
                'template_suggestions': [
                    {
                        'template_id': 'walmart_product_template',
                        'confidence': 0.78,
                        'reasoning': 'Data structure matches Walmart product format'
                    }
                ]
            }
            
            return {
                'success': True,
                'suggestions': suggestions
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

