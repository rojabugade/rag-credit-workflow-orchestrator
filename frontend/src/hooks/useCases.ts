import {useQuery} from "@tanstack/react-query";
import {api} from "../services/api";

export function useCases() {
  const query = useQuery({queryKey: ["applications"], queryFn: api.listCases});
  const refresh = async () => { await query.refetch(); };
  return {cases: query.data ?? [], loading: query.isLoading, error: query.error ? String(query.error) : "", refresh};
}
