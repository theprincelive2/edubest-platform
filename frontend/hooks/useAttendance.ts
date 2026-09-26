import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api";
import type { AttendanceSession, AttendanceStatus, PaginatedResponse } from "@/types";

export interface MarkAttendancePayload {
  class_room?: string;
  class_obj?: string;
  date: string;
  period?: "morning" | "afternoon" | "full_day";
  term?: string;
  records: {
    student_id: string;
    status: AttendanceStatus;
    remark?: string;
  }[];
}

export function useAttendance(filters?: Record<string, string>) {
  return useQuery<PaginatedResponse<AttendanceSession>>({
    queryKey: ["attendance-sessions", filters],
    queryFn: () => {
      const params = new URLSearchParams(filters).toString();
      return apiGet<PaginatedResponse<AttendanceSession>>(`/attendance/sessions/?${params}`);
    },
  });
}

export function useMarkAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MarkAttendancePayload) =>
      apiPost<{ success: boolean; message: string }>("/attendance/sessions/mark/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance-sessions"] });
    },
  });
}
