import { useQuery } from "@tanstack/react-query";
import useAxios from "../hooks/useAxios";
import { roomUrl } from "../utils/apiurl";

export const KEY = "room";

export default function useRoomQuery(roomId: string | undefined) {
  const api = useAxios();

  return useQuery({
    queryKey: [KEY, roomId],
    queryFn: async ({ queryKey }) => {
      const [_, roomId] = queryKey;
      const res = await api.get(roomUrl.getRoomById(roomId));
      return res.data;
    },
  });
}
