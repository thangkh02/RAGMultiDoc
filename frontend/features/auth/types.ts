export type AuthUser = {
  id: string;
  name: string;
  email: string;
};

export type AuthCredentials = {
  name?: string;
  email: string;
  password: string;
};
