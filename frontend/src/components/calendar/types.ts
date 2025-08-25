// Shared types for calendar components
export interface CalendarEvent {
  id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  event_type: string;
  priority: string;
  goal_id?: number;
  is_synced?: boolean;
}

export interface Goal {
  id: number;
  title: string;
  category: string;
  status: string;
}

export interface RoutineSettings {
  wake_up_time: string;
  sleep_time: string;
  gym_time: string;
  lunch_time: string;
  dinner_time: string;
  work_start: string;
  work_end: string;
  break_duration: number;
  focus_block_duration: number;
}

export interface AICalendarFormData {
  title: string;
  description: string;
  duration_minutes: number;
  event_type: string;
  priority: string;
  goal_id?: number;
}

export interface ChatMessage {
  role: string;
  content: string;
}