import { useMutation, useQueryClient } from "@tanstack/react-query";
import { submitScan } from "../api/scans";

export function useScanSubmit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => submitScan(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-history"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });
}
