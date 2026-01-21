export type RegistryForm = {
  code: string;
  label: string;
  form_model_path: string;
};

export type RegistrySample = {
  id: string;
  form_code: string;
  kind: string;
  filename: string;
  path: string;
};

export type RegistrySnapshot = {
  forms: RegistryForm[];
  samples: RegistrySample[];
};
