export const baseUrl = "http://ec2-54-85-121-209.compute-1.amazonaws.com"
export const initalTag = "api";
export const apiVersion = "v1";
export const baseTag = `${initalTag}/${apiVersion}`;

export const authTag = "auth/token";
export const authUrl = {
  loginUser: `/${baseTag}/${authTag}/`,
  refreshToken: `/${baseTag}/${authTag}/refresh/`,
  blacklistedToken: `/${baseTag}/${authTag}/blacklisted/`,
  outstandingToken: `/${baseTag}/${authTag}/outstanding/`,
  deleteTokenAll: `/${baseTag}/${authTag}/deleteall/`,
};

export const messageTag = "message";
export const messageUrl = {
  roomMessage: (roomId: string | undefined, offset: number, limit: number) =>
    `/${baseTag}/${messageTag}/msg/${roomId}/?offset=${offset}&limit=${limit}`,
};

export const roomTag = "room";
export const roomUrl = {
  getRoom: `/${baseTag}/${roomTag}/`,
  chatHistory: `/${baseTag}/${roomTag}/history/`,
  initialRoom: `/${baseTag}/${roomTag}/initialRoom/`,

  getRoomById: (roomId: string | undefined) =>
    `/${baseTag}/${roomTag}/room/${roomId}/`,

  getRoomFriends: (roomId: string | undefined) =>
    `/${baseTag}/${roomTag}/friend/${roomId}/`,
};

export const userTag = "user";
type searchUser = {
  searchType: string;
  search: string;
  limit: number;
  offset: number;
};
export const userUrl = {
  getUser: (uid?: string, user_id?: number) => {
    if (uid) {
      return `/${baseTag}/${userTag}/getuser/?uid=${uid}`;
    } else if (user_id) {
      return `/${baseTag}/${userTag}/getuser/?user_id=${user_id}`;
    }
    return `/${baseTag}/${userTag}/getuser/`;
  },

  createUser: `/${baseTag}/${userTag}/createuser/`,
  updateUser: `/${baseTag}/${userTag}/updateuser/`,
  uploadProfile: `/${baseTag}/${userTag}/upload/profile/`,
  updateUserName: `/${baseTag}/${userTag}/updateusername/`,
  updatePassword: `/${baseTag}/${userTag}/updatepassword/`,
  deleteUser: `/${baseTag}/${userTag}/deleteuser/`,

  searchUser: (query: searchUser) =>
    `/${baseTag}/${userTag}/search/?search_type=${query.searchType}&search=${query.search}&limit=${query.limit}&offset=${query.offset}`,
  onlineUser: `/${baseTag}/${userTag}/onlineuser/`,
};

export const notificationTag = "notification";
export const notificationUrl = {
  getNotification: (limit: number = 10, offset: number = 0) =>
    `/${baseTag}/${notificationTag}/?limit=${limit}&offset=${offset}`,

  markOrChangeStatus: (notificationId: number) =>
    `/${baseTag}/${notificationTag}/${notificationId}`,

  markAllRead: `/${baseTag}/${notificationTag}/mark/read/all`,

  notificationDelete: (notificationId: number) =>
    `/${baseTag}/${notificationTag}/delete/${notificationId}/`,

  deleteAll: `/${baseTag}/${notificationTag}/all/delete/`,
};

export const relationTag = "relation";
export const relationUrl = {
  acceptFriendRequest: (userId: number) =>
    `/${baseTag}/${relationTag}/accept/${userId}/`,

  request: (userId: number) => `/${baseTag}/${relationTag}/request/${userId}/`,

  cancelRequest: (userId: number) =>
    `/${baseTag}/${relationTag}/cancelrequest/${userId}/`,

  unfriend: (userId: number) =>
    `/${baseTag}/${relationTag}/unfriend/${userId}/`,

  block: (userId: number) => `/${baseTag}/${relationTag}/block/${userId}/`,

  unblock: (userId: number) => `/${baseTag}/${relationTag}/unblock/${userId}/`,
};
