import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { PaginatedResponse, Student, StudentFilters } from "@/types";

export function useStudents(filters?: StudentFilters) {
  return useQuery<PaginatedResponse<Student>>({
    queryKey: ["students", filters],
    queryFn: () => {
      const params = new URLSearchParams(
        Object.entries(filters || {}).reduce((acc, [k, v]) => {
          if (v !== undefined && v !== null && v !== "") acc[k] = String(v);
          return acc;
        }, {} as Record<string, string>)
      ).toString();
      return apiGet<PaginatedResponse<Student>>(`/students/?${params}`);
    },
  });
}

export function useStudent(id: string) {
  return useQuery<Student>({
    queryKey: ["student", id],
    queryFn: () => apiGet<Student>(`/students/${id}/`),
    enabled: Boolean(id),
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Student> | Record<string, any>) => apiPost<Student>("/students/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}

export function useUpdateStudent(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Student> | Record<string, any>) => apiPut<Student>(`/students/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["student", id] });
    },
  });
}

export function useDeleteStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/students/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}
