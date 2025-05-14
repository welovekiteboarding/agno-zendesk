// agno-zendesk/frontend__backup2/protocol/uiInstruction.ts
import schema from "../../schemas/ui_instruction.schema.json" with { type: "json" };

export type UIInstructionType =
  | "show_file_upload"
  | "request_email"
  | "display_form"
  | "show_auth_prompt"
  | "show_selection_menu"
  | "show_progress_indicator"
  | "show_confirmation_dialog";

export interface UIInstructionMetadata {
  priority: "low" | "normal" | "high";
  sequence?: number;
  version: string;
  agent_id?: string;
}

export interface UIInstruction {
  instruction_type: UIInstructionType;
  parameters: Record<string, any>;
  metadata: UIInstructionMetadata;
}

export class UIInstructionValidationError extends Error {}

export function validateUIInstruction(message: any): void {
  // Basic structure validation
  if (
    !message ||
    typeof message !== "object" ||
    typeof message.instruction_type !== "string" ||
    typeof message.parameters !== "object" ||
    typeof message.metadata !== "object"
  ) {
    throw new UIInstructionValidationError("Invalid UIInstruction structure");
  }

  // Validate instruction type
  if (
    ![
      "show_file_upload",
      "request_email",
      "display_form",
      "show_auth_prompt",
      "show_selection_menu",
      "show_progress_indicator",
      "show_confirmation_dialog",
    ].includes(message.instruction_type)
  ) {
    throw new UIInstructionValidationError(
      `Unknown instruction_type: ${message.instruction_type}`
    );
  }

  // Validate metadata
  if (!message.metadata.priority) {
    throw new UIInstructionValidationError("Missing priority in metadata");
  }
  if (!["low", "normal", "high"].includes(message.metadata.priority)) {
    throw new UIInstructionValidationError(
      `Invalid priority: ${message.metadata.priority}`
    );
  }
  if (
    typeof message.metadata.version !== "string" ||
    !/^\d+\.\d+\.\d+$/.test(message.metadata.version)
  ) {
    throw new UIInstructionValidationError(
      `Invalid version: ${message.metadata.version}`
    );
  }
  if (message.metadata.sequence !== undefined && 
      (typeof message.metadata.sequence !== "number" || message.metadata.sequence < 0)) {
    throw new UIInstructionValidationError(
      `Invalid sequence: ${message.metadata.sequence}`
    );
  }

  // Instruction-specific validation
  switch (message.instruction_type) {
    case "show_file_upload":
      validateFileUploadParams(message.parameters);
      break;
    case "request_email":
      validateEmailRequestParams(message.parameters);
      break;
    case "display_form":
      validateFormParams(message.parameters);
      break;
  }
}

function validateFileUploadParams(params: any): void {
  if (!params.max_files || typeof params.max_files !== "number" || params.max_files <= 0) {
    throw new UIInstructionValidationError("Invalid max_files parameter");
  }
  if (!params.max_size_mb || typeof params.max_size_mb !== "number" || params.max_size_mb <= 0) {
    throw new UIInstructionValidationError("Invalid max_size_mb parameter");
  }
  if (!Array.isArray(params.accepted_types) || params.accepted_types.length === 0) {
    throw new UIInstructionValidationError("Invalid accepted_types parameter");
  }
  if (!params.upload_url || !isValidUrl(params.upload_url)) {
    throw new UIInstructionValidationError("Invalid upload_url parameter");
  }
}

function validateEmailRequestParams(params: any): void {
  if (!params.prompt || typeof params.prompt !== "string" || params.prompt.trim() === "") {
    throw new UIInstructionValidationError("Invalid prompt parameter");
  }
  if (params.validation_regex && !isValidRegex(params.validation_regex)) {
    throw new UIInstructionValidationError("Invalid validation_regex parameter");
  }
}

function validateFormParams(params: any): void {
  if (!Array.isArray(params.fields) || params.fields.length === 0) {
    throw new UIInstructionValidationError("Invalid fields parameter");
  }
  
  params.fields.forEach((field: any, index: number) => {
    if (!field.name || typeof field.name !== "string") {
      throw new UIInstructionValidationError(`Invalid field name at index ${index}`);
    }
    if (!field.label || typeof field.label !== "string") {
      throw new UIInstructionValidationError(`Invalid field label at index ${index}`);
    }
    if (!field.type || typeof field.type !== "string") {
      throw new UIInstructionValidationError(`Invalid field type at index ${index}`);
    }
    if (field.required !== undefined && typeof field.required !== "boolean") {
      throw new UIInstructionValidationError(`Invalid required flag at index ${index}`);
    }
  });
}

function isValidUrl(urlString: string): boolean {
  try {
    new URL(urlString);
    return true;
  } catch {
    return false;
  }
}

function isValidRegex(pattern: string): boolean {
  try {
    new RegExp(pattern);
    return true;
  } catch {
    return false;
  }
}

export function serializeUIInstruction(
  instruction: UIInstruction,
  pretty = false
): string {
  validateUIInstruction(instruction);
  return JSON.stringify(instruction, null, pretty ? 2 : undefined);
}

export function deserializeUIInstruction(jsonStr: string): UIInstruction {
  let obj: any;
  try {
    obj = JSON.parse(jsonStr);
  } catch (e) {
    throw new UIInstructionValidationError("Invalid JSON");
  }
  validateUIInstruction(obj);
  return obj as UIInstruction;
}

// Example usage (for testing)
if (typeof window === "undefined") {
  // Node.js only
  const example: UIInstruction = {
    instruction_type: "show_file_upload",
    parameters: {
      max_files: 3,
      max_size_mb: 100,
      accepted_types: ["image/png", "image/jpeg", "video/mp4"],
      upload_url: "https://example.com/upload",
    },
    metadata: {
      priority: "high",
      sequence: 1,
      version: "1.0.0",
      agent_id: "form_collector",
    },
  };
  const jsonStr = serializeUIInstruction(example, true);
  console.log("Serialized:", jsonStr);
  const parsed = deserializeUIInstruction(jsonStr);
  console.log("Deserialized:", parsed);
}
