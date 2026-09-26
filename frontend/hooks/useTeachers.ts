import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { PaginatedResponse, Teacher, TeacherFilters } from "@/types";

export function useTeachers(filters?: TeacherFilters) {
  return useQuery<PaginatedResponse<Teacher>>({
    queryKey: ["teachers", filters],
    queryFn: () => {
      const params = new URLSearchParams(
        Object.entries(filters || {}).reduce((acc, [k, v]) => {
          if (v !== undefined && v !== null && v !== "") acc[k] = String(v);
          return acc;
        }, {} as Record<string, string>)
      ).toString();
      return apiGet<PaginatedResponse<Teacher>>(`/teachers/?${params}`);
    },
  });
}

export function useTeacher(id: string) {
  return useQuery<Teacher>({
    queryKey: ["teacher", id],
    queryFn: () => apiGet<Teacher>(`/teachers/${id}/`),
    enabled: Boolean(id),
  });
}

export function useCreateTeacher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Teacher>) => apiPost<Teacher>("/teachers/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
    },
  });
}
