# =============================================================================
# SIMULATION SCHEDULER — Discrete Event Scheduling System
# =============================================================================
"""
Handles time-based event scheduling for simulations:
- Priority queue for event ordering
- Support for simultaneous events
- Event cancellation and rescheduling
- Parallel execution coordination
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable, Tuple
import heapq


class EventType(Enum):
    """Types of simulation events."""
    AGENT_UPDATE = auto()      # Agent state update
    AGENT_INTERACTION = auto() # Agent-to-agent interaction
    WORLD_EVENT = auto()       # External world event
    CHECKPOINT = auto()        # Save simulation state
    METRICS_COLLECTION = auto() # Collect statistics
    CUSTOM = auto()            # User-defined event


@dataclass(order=True)
class SimulationEvent:
    """
    A scheduled event in the simulation.
    
    Events are ordered by (time, priority) for deterministic execution.
    
    Attributes:
        scheduled_time: When the event should occur
        priority: Execution priority (lower = higher priority)
        event_type: Type of event
        handler: Function to execute when event fires
        args: Positional arguments for handler
        kwargs: Keyword arguments for handler
        event_id: Unique identifier
        cancelable: Whether event can be cancelled
        recurring: Whether event repeats
        recurrence_interval: Time between recurrences
    """
    scheduled_time: datetime
    priority: int = 0
    event_type: EventType = EventType.CUSTOM
    handler: Optional[Callable] = field(compare=False, default=None)
    args: tuple = field(compare=False, default_factory=tuple)
    kwargs: Dict[str, Any] = field(compare=False, default_factory=dict)
    event_id: str = field(compare=False, default_factory=lambda: id(object()))
    cancelable: bool = field(compare=False, default=True)
    recurring: bool = field(compare=False, default=False)
    recurrence_interval: Optional[timedelta] = field(compare=False, default=None)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)
    
    def execute(self) -> Any:
        """Execute the event handler."""
        if self.handler is None:
            return None
        return self.handler(*self.args, **self.kwargs)
    
    def reschedule(self, new_time: datetime):
        """Update scheduled time."""
        self.scheduled_time = new_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "scheduled_time": self.scheduled_time.isoformat(),
            "priority": self.priority,
            "event_type": self.event_type.name,
            "event_id": self.event_id,
            "cancelable": self.cancelable,
            "recurring": self.recurring,
            "recurrence_interval": self.recurrence_interval.total_seconds() if self.recurrence_interval else None,
            "metadata": self.metadata.copy()
        }


class SimulationScheduler:
    """
    Discrete event scheduler for simulation time management.
    
    Features:
    - Priority-based event ordering
    - Deterministic execution order
    - Event cancellation and modification
    - Recurring events
    - Checkpoint integration
    
    Usage:
        scheduler = SimulationScheduler(start_time=datetime.now())
        scheduler.schedule(my_handler, delay=timedelta(hours=1))
        next_event = scheduler.pop_next()
        scheduler.execute(next_event)
    """
    
    def __init__(self, start_time: Optional[datetime] = None):
        """
        Initialize scheduler.
        
        Args:
            start_time: Simulation start time
        """
        self.start_time = start_time or datetime.now()
        self.current_time = self.start_time
        
        # Priority queue: (time, priority, sequence, event)
        self._queue: List[Tuple[datetime, int, int, SimulationEvent]] = []
        self._sequence = 0  # For stable sorting of simultaneous events
        
        # Event tracking
        self._cancelled_ids: set = set()
        self._event_registry: Dict[str, SimulationEvent] = {}
        
        # Statistics
        self.events_processed = 0
        self.events_scheduled = 0
    
    def schedule(self, handler: Callable, 
                 delay: Optional[timedelta] = None,
                 at_time: Optional[datetime] = None,
                 priority: int = 0,
                 event_type: EventType = EventType.CUSTOM,
                 args: tuple = (),
                 kwargs: Optional[Dict[str, Any]] = None,
                 cancelable: bool = True,
                 recurring: bool = False,
                 recurrence_interval: Optional[timedelta] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a new event.
        
        Args:
            handler: Function to call when event fires
            delay: Time delta from current time
            at_time: Absolute time (alternative to delay)
            priority: Execution priority (lower = higher priority)
            event_type: Type of event
            args: Handler positional arguments
            kwargs: Handler keyword arguments
            cancelable: Whether event can be cancelled
            recurring: Whether event should repeat
            recurrence_interval: Time between recurrences
            metadata: Additional event data
        
        Returns:
            Event ID for later reference
        """
        # Calculate scheduled time
        if at_time is not None:
            scheduled_time = at_time
        elif delay is not None:
            scheduled_time = self.current_time + delay
        else:
            scheduled_time = self.current_time
        
        event = SimulationEvent(
            scheduled_time=scheduled_time,
            priority=priority,
            event_type=event_type,
            handler=handler,
            args=args,
            kwargs=kwargs or {},
            cancelable=cancelable,
            recurring=recurring,
            recurrence_interval=recurrence_interval,
            metadata=metadata or {}
        )
        
        # Add to priority queue
        heapq.heappush(self._queue, (scheduled_time, priority, self._sequence, event))
        self._sequence += 1
        self._event_registry[event.event_id] = event
        self.events_scheduled += 1
        
        return event.event_id
    
    def pop_next(self) -> Optional[SimulationEvent]:
        """
        Get and remove the next event from the queue.
        
        Returns:
            Next event or None if queue is empty
        """
        while self._queue:
            _, _, _, event = heapq.heappop(self._queue)
            
            # Skip cancelled events
            if event.event_id in self._cancelled_ids:
                self._cancelled_ids.discard(event.event_id)
                continue
            
            # Remove from registry
            self._event_registry.pop(event.event_id, None)
            
            # Update current time
            self.current_time = event.scheduled_time
            
            # Handle recurring events
            if event.recurring and event.recurrence_interval:
                self.schedule(
                    handler=event.handler,
                    at_time=event.scheduled_time + event.recurrence_interval,
                    priority=event.priority,
                    event_type=event.event_type,
                    args=event.args,
                    kwargs=event.kwargs,
                    cancelable=event.cancelable,
                    recurring=True,
                    recurrence_interval=event.recurrence_interval,
                    metadata=event.metadata
                )
            
            self.events_processed += 1
            return event
        
        return None
    
    def peek_next(self) -> Optional[SimulationEvent]:
        """
        Get the next event without removing it.
        
        Returns:
            Next event or None if queue is empty
        """
        while self._queue:
            _, _, _, event = self._queue[0]
            if event.event_id in self._cancelled_ids:
                heapq.heappop(self._queue)
                self._cancelled_ids.discard(event.event_id)
                continue
            return event
        return None
    
    def execute_next(self) -> Optional[Any]:
        """
        Execute the next event.
        
        Returns:
            Event handler result or None
        """
        event = self.pop_next()
        if event:
            return event.execute()
        return None
    
    def run_until(self, end_time: datetime, 
                  max_events: Optional[int] = None) -> int:
        """
        Run all events until specified time.
        
        Args:
            end_time: Stop time
            max_events: Maximum events to process
        
        Returns:
            Number of events processed
        """
        count = 0
        while True:
            if max_events and count >= max_events:
                break
            
            next_event = self.peek_next()
            if not next_event or next_event.scheduled_time > end_time:
                break
            
            self.execute_next()
            count += 1
        
        return count
    
    def run_for(self, duration: timedelta, 
                max_events: Optional[int] = None) -> int:
        """
        Run events for specified duration.
        
        Args:
            duration: Time span to simulate
            max_events: Maximum events to process
        
        Returns:
            Number of events processed
        """
        end_time = self.current_time + duration
        return self.run_until(end_time, max_events)
    
    def cancel(self, event_id: str) -> bool:
        """
        Cancel a scheduled event.
        
        Args:
            event_id: ID of event to cancel
        
        Returns:
            True if event was found and cancelled
        """
        event = self._event_registry.get(event_id)
        if event and event.cancelable:
            self._cancelled_ids.add(event_id)
            return True
        return False
    
    def get_events_at(self, time: datetime) -> List[SimulationEvent]:
        """Get all events scheduled at a specific time."""
        return [
            e for _, _, _, e in self._queue
            if e.scheduled_time == time and e.event_id not in self._cancelled_ids
        ]
    
    def get_events_between(self, start: datetime, end: datetime) -> List[SimulationEvent]:
        """Get all events in a time range."""
        return [
            e for _, _, _, e in self._queue
            if start <= e.scheduled_time <= end and e.event_id not in self._cancelled_ids
        ]
    
    def get_pending_count(self) -> int:
        """Get number of pending (non-cancelled) events."""
        return len(self._queue) - len(self._cancelled_ids)
    
    def clear(self):
        """Clear all pending events."""
        self._queue.clear()
        self._cancelled_ids.clear()
        self._event_registry.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "current_time": self.current_time.isoformat(),
            "start_time": self.start_time.isoformat(),
            "events_scheduled": self.events_scheduled,
            "events_processed": self.events_processed,
            "pending_events": self.get_pending_count(),
            "queue_depth": len(self._queue)
        }
