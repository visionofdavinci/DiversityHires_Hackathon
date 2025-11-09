import { useState, useEffect } from 'react';
import { CalendarSlot } from '@/types';
import { api } from '@/services/api';

interface CalendarViewProps {
  username: string;
  onSlotsUpdate?: (slots: CalendarSlot[]) => void;
}

export default function CalendarView({ username, onSlotsUpdate }: CalendarViewProps) {
  const [freeSlots, setFreeSlots] = useState<CalendarSlot[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFreeSlots = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const slots = await api.getCalendarFreeSlots(username);
        setFreeSlots(slots);
        onSlotsUpdate?.(slots);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load calendar slots');
      } finally {
        setIsLoading(false);
      }
    };

    loadFreeSlots();
  }, [username, onSlotsUpdate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Available Time Slots</h2>
      <div className="grid gap-3">
        {freeSlots.map((slot, index) => (
          <div
            key={index}
            className="p-4 bg-white shadow rounded-lg hover:shadow-md transition-shadow"
          >
            <p className="font-medium">
              {new Date(slot.start).toLocaleDateString()} 
            </p>
            <p className="text-gray-600">
              {new Date(slot.start).toLocaleTimeString()} - 
              {new Date(slot.end).toLocaleTimeString()}
            </p>
          </div>
        ))}
      </div>
      {freeSlots.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No free time slots available
        </p>
      )}
    </div>
  );
}