"""
Unit tests for EC2 service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.aws.ec2_service import EC2Service


class TestEC2Service:
    """Test EC2Service class"""
    
    def test_list_instances_success(self, db_session, mock_aws_client, sample_user_data):
        """Test successful instance listing"""
        # Create user
        from database import User
        from utils.auth import AuthManager
        
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=AuthManager.get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock AWS response
        mock_response = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-1234567890abcdef0',
                    'State': {'Name': 'running'},
                    'InstanceType': 't2.micro',
                    'ImageId': 'ami-12345678',
                    'Tags': [{'Key': 'Name', 'Value': 'Test Instance'}]
                }]
            }]
        }
        
        with patch('services.aws.ec2_service.EC2Service.client') as mock_client:
            mock_client.describe_instances.return_value = mock_response
            
            ec2_service = EC2Service(db_session, user.id)
            result = ec2_service.list_instances()
            
            assert result['success'] is True
            assert len(result['instances']) == 1
            assert result['instances'][0]['instance_id'] == 'i-1234567890abcdef0'
    
    def test_create_instance_validation(self, db_session, sample_user_data):
        """Test instance creation validation"""
        from database import User
        from utils.auth import AuthManager
        
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=AuthManager.get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        ec2_service = EC2Service(db_session, user.id)
        
        # Missing required parameter
        result = ec2_service.create_instance({'InstanceType': 't2.micro'})
        assert result['success'] is False
        assert 'ImageId' in result.get('error', '')
        
        # Invalid AMI format
        result = ec2_service.create_instance({
            'ImageId': 'invalid-ami',
            'InstanceType': 't2.micro'
        })
        assert result['success'] is False
