"""Daily scheduled tasks for research crawler."""
import asyncio
from typing import Optional, Callable
from datetime import datetime, time
from pathlib import Path
import json


class ResearchScheduler:
    """Scheduler for daily research crawling tasks."""
    
    def __init__(self, state_file: Optional[str] = None):
        """Initialize scheduler.
        
        Args:
            state_file: Path to file storing scheduler state
        """
        self.state_file = state_file or ".research_scheduler_state.json"
        self._scheduled_task: Optional[asyncio.Task] = None
        self._running = False
    
    def save_last_crawl_date(self, date: datetime):
        """Save last crawl date to state file.
        
        Args:
            date: Last crawl date
        """
        try:
            state_path = Path(self.state_file)
            state = {
                'last_crawl_date': date.isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            with open(state_path, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"⚠️  Failed to save scheduler state: {e}")
    
    def load_last_crawl_date(self) -> Optional[datetime]:
        """Load last crawl date from state file.
        
        Returns:
            Last crawl date or None
        """
        try:
            state_path = Path(self.state_file)
            if state_path.exists():
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    date_str = state.get('last_crawl_date')
                    if date_str:
                        return datetime.fromisoformat(date_str)
        except Exception as e:
            print(f"⚠️  Failed to load scheduler state: {e}")
        return None
    
    async def _wait_until_time(self, target_time: time):
        """Wait until target time.
        
        Args:
            target_time: Target time of day
        """
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), target_time)
        
        # If target time has passed today, schedule for tomorrow
        if target_datetime <= now:
            target_datetime = target_datetime.replace(day=target_datetime.day + 1)
        
        # Calculate seconds until target
        delta = (target_datetime - now).total_seconds()
        await asyncio.sleep(delta)
    
    async def _daily_loop(
        self,
        crawl_func: Callable,
        crawl_time: time = time(2, 0)  # 2 AM default
    ):
        """Run daily crawl loop.
        
        Args:
            crawl_func: Async function to call for crawling
            crawl_time: Time of day to run crawl (default: 2 AM)
        """
        self._running = True
        
        while self._running:
            try:
                # Wait until crawl time
                await self._wait_until_time(crawl_time)
                
                # Run crawl
                print(f"🕐 Running scheduled daily crawl at {datetime.now()}")
                await crawl_func()
                
                # Update last crawl date
                self.save_last_crawl_date(datetime.now())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in scheduled crawl: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    def schedule_daily_crawl(
        self,
        crawl_func: Callable,
        crawl_time: str = "02:00"
    ) -> asyncio.Task:
        """Schedule daily crawl task.
        
        Args:
            crawl_func: Async function to call for crawling
            crawl_time: Time string in HH:MM format (default: "02:00")
            
        Returns:
            asyncio.Task for the scheduled task
        """
        # Parse time string
        try:
            hour, minute = map(int, crawl_time.split(':'))
            target_time = time(hour, minute)
        except ValueError:
            print(f"⚠️  Invalid time format '{crawl_time}', using default 02:00")
            target_time = time(2, 0)
        
        # Create and start task
        self._scheduled_task = asyncio.create_task(
            self._daily_loop(crawl_func, target_time)
        )
        
        print(f"✓ Scheduled daily crawl for {crawl_time}")
        return self._scheduled_task
    
    async def run_daily_crawl(self, crawl_func: Callable):
        """Run crawl immediately (for testing or manual execution).
        
        Args:
            crawl_func: Async function to call for crawling
        """
        print("🔄 Running manual daily crawl...")
        await crawl_func()
        self.save_last_crawl_date(datetime.now())
    
    def stop(self):
        """Stop scheduled crawls."""
        self._running = False
        if self._scheduled_task:
            self._scheduled_task.cancel()
            print("✓ Stopped scheduled crawls")
    
    def is_running(self) -> bool:
        """Check if scheduler is running.
        
        Returns:
            True if scheduler is active
        """
        return self._running and self._scheduled_task is not None and not self._scheduled_task.done()

