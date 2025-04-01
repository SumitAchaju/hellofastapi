import { useQuery } from "@tanstack/react-query";
import useAxios from "../hooks/useAxios";
import { userUrl } from "../utils/apiurl";

const KEY = ["onlineUsers"];

export default function useOnlineUserQuery() {
  const api = useAxios();
  const { data, isSuccess, isLoading, isError, error } = useQuery({
    queryKey: KEY,
    queryFn: async () => {
      const fetch = await api.get(userUrl.onlineUser);
      return fetch.data;
    },
  });

  return { data, isSuccess, isLoading, isError, error };
}
