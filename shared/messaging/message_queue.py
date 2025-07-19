"""
Redis-based messaging system for inter-agent communication
"""

import json
import redis
import uuid
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    """Types of messages that can be sent between agents"""
    TASK_NOTIFICATION = "task_notification"
    STATUS_UPDATE = "status_update"
    ERROR_ALERT = "error_alert"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    CONFIG_CHANGE = "config_change"
    HEALTH_CHECK = "health_check"
    SHUTDOWN = "shutdown"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Message:
    """Message structure for inter-agent communication"""
    id: str
    timestamp: str
    source_agent: str
    target_agent: str
    message_type: MessageType
    priority: MessagePriority
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    expires_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict:
        """Convert message to dictionary for JSON serialization"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

class MessageQueue:
    """Redis-based message queue for agent communication"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )
        self.subscribers = {}
        self.running = False
        self.worker_thread = None
        
    def connect(self) -> bool:
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def send_message(self, message: Message) -> bool:
        """Send a message to the queue"""
        try:
            # Store message in Redis with expiration
            message_key = f"message:{message.id}"
            message_data = json.dumps(message.to_dict())
            
            # Set expiration time (default 24 hours if not specified)
            if message.expires_at:
                expires_at = datetime.fromisoformat(message.expires_at)
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
            else:
                ttl = 86400  # 24 hours
            
            # Store message
            self.redis_client.setex(message_key, ttl, message_data)
            
            # Add to agent's queue
            agent_queue = f"queue:{message.target_agent}"
            self.redis_client.lpush(agent_queue, message.id)
            
            # Add to priority queue if high priority
            if message.priority in [MessagePriority.HIGH, MessagePriority.URGENT]:
                priority_queue = f"priority:{message.target_agent}"
                self.redis_client.lpush(priority_queue, message.id)
            
            # Publish notification
            channel = f"notifications:{message.target_agent}"
            notification = {
                'message_id': message.id,
                'message_type': message.message_type.value,
                'priority': message.priority.value,
                'source_agent': message.source_agent
            }
            self.redis_client.publish(channel, json.dumps(notification))
            
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def receive_message(self, agent_id: str, timeout: int = 1) -> Optional[Message]:
        """Receive a message from the queue"""
        try:
            # Check priority queue first
            priority_queue = f"priority:{agent_id}"
            message_id = self.redis_client.brpop(priority_queue, timeout=0.1)
            
            if not message_id:
                # Check regular queue
                agent_queue = f"queue:{agent_id}"
                message_id = self.redis_client.brpop(agent_queue, timeout=timeout)
            
            if message_id:
                message_id = message_id[1]  # Extract the actual ID
                message_key = f"message:{message_id}"
                message_data = self.redis_client.get(message_key)
                
                if message_data:
                    # Delete message after retrieval
                    self.redis_client.delete(message_key)
                    return Message.from_dict(json.loads(message_data))
            
            return None
            
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
    
    def subscribe_to_notifications(self, agent_id: str, callback: Callable[[Dict], None]):
        """Subscribe to real-time notifications"""
        channel = f"notifications:{agent_id}"
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel)
        
        def notification_worker():
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        notification_data = json.loads(message['data'])
                        callback(notification_data)
                    except Exception as e:
                        print(f"Error processing notification: {e}")
        
        thread = threading.Thread(target=notification_worker, daemon=True)
        thread.start()
        return pubsub
    
    def get_queue_size(self, agent_id: str) -> Dict[str, int]:
        """Get queue sizes for an agent"""
        regular_queue = f"queue:{agent_id}"
        priority_queue = f"priority:{agent_id}"
        
        return {
            'regular': self.redis_client.llen(regular_queue),
            'priority': self.redis_client.llen(priority_queue),
            'total': self.redis_client.llen(regular_queue) + self.redis_client.llen(priority_queue)
        }
    
    def clear_queue(self, agent_id: str):
        """Clear all messages for an agent"""
        regular_queue = f"queue:{agent_id}"
        priority_queue = f"priority:{agent_id}"
        
        self.redis_client.delete(regular_queue)
        self.redis_client.delete(priority_queue)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status information for an agent"""
        status_key = f"status:{agent_id}"
        status_data = self.redis_client.get(status_key)
        
        if status_data:
            return json.loads(status_data)
        return {}
    
    def update_agent_status(self, agent_id: str, status: Dict[str, Any]):
        """Update status information for an agent"""
        status_key = f"status:{agent_id}"
        status_data = json.dumps(status)
        self.redis_client.setex(status_key, 300, status_data)  # 5 minute TTL

class AgentCommunicator:
    """High-level interface for agent communication"""
    
    def __init__(self, agent_id: str, message_queue: MessageQueue):
        self.agent_id = agent_id
        self.message_queue = message_queue
        self.message_handlers = {}
        self.running = False
        self.worker_thread = None
    
    def register_handler(self, message_type: MessageType, handler: Callable[[Message], None]):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
    
    def send_task_notification(self, target_agent: str, task_data: Dict[str, Any], 
                             priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a task notification to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source_agent=self.agent_id,
            target_agent=target_agent,
            message_type=MessageType.TASK_NOTIFICATION,
            priority=priority,
            payload=task_data
        )
        
        if self.message_queue.send_message(message):
            return message.id
        return None
    
    def send_status_update(self, target_agent: str, status_data: Dict[str, Any]):
        """Send a status update to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source_agent=self.agent_id,
            target_agent=target_agent,
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.NORMAL,
            payload=status_data
        )
        
        return self.message_queue.send_message(message)
    
    def send_error_alert(self, target_agent: str, error_data: Dict[str, Any]):
        """Send an error alert to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source_agent=self.agent_id,
            target_agent=target_agent,
            message_type=MessageType.ERROR_ALERT,
            priority=MessagePriority.HIGH,
            payload=error_data
        )
        
        return self.message_queue.send_message(message)
    
    def request_data(self, target_agent: str, request_data: Dict[str, Any], 
                    correlation_id: str = None) -> str:
        """Request data from another agent"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        message = Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source_agent=self.agent_id,
            target_agent=target_agent,
            message_type=MessageType.DATA_REQUEST,
            priority=MessagePriority.NORMAL,
            payload=request_data,
            correlation_id=correlation_id
        )
        
        if self.message_queue.send_message(message):
            return correlation_id
        return None
    
    def send_data_response(self, target_agent: str, response_data: Dict[str, Any], 
                          correlation_id: str):
        """Send a data response to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source_agent=self.agent_id,
            target_agent=target_agent,
            message_type=MessageType.DATA_RESPONSE,
            priority=MessagePriority.NORMAL,
            payload=response_data,
            correlation_id=correlation_id
        )
        
        return self.message_queue.send_message(message)
    
    def broadcast_message(self, agent_list: List[str], message_type: MessageType, 
                         payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """Broadcast a message to multiple agents"""
        message_ids = []
        
        for target_agent in agent_list:
            message = Message(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat(),
                source_agent=self.agent_id,
                target_agent=target_agent,
                message_type=message_type,
                priority=priority,
                payload=payload
            )
            
            if self.message_queue.send_message(message):
                message_ids.append(message.id)
        
        return message_ids
    
    def start_listening(self):
        """Start listening for messages"""
        self.running = True
        
        def message_worker():
            while self.running:
                try:
                    message = self.message_queue.receive_message(self.agent_id, timeout=1)
                    if message and message.message_type in self.message_handlers:
                        handler = self.message_handlers[message.message_type]
                        handler(message)
                except Exception as e:
                    print(f"Error processing message: {e}")
        
        self.worker_thread = threading.Thread(target=message_worker, daemon=True)
        self.worker_thread.start()
    
    def stop_listening(self):
        """Stop listening for messages"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def update_status(self, status: Dict[str, Any]):
        """Update this agent's status"""
        status['agent_id'] = self.agent_id
        status['last_updated'] = datetime.utcnow().isoformat()
        self.message_queue.update_agent_status(self.agent_id, status)

# Utility functions for common messaging patterns
def create_message_queue(redis_config: Dict[str, Any] = None) -> MessageQueue:
    """Create a message queue with default or custom Redis configuration"""
    if redis_config is None:
        redis_config = {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0
        }
    
    return MessageQueue(**redis_config)

def create_agent_communicator(agent_id: str, redis_config: Dict[str, Any] = None) -> AgentCommunicator:
    """Create an agent communicator with default configuration"""
    message_queue = create_message_queue(redis_config)
    return AgentCommunicator(agent_id, message_queue)

