import { z, ZodSchema, ZodError } from "zod";

export interface ValidationResult {
  success: boolean;
  errors: Record<string, string[]>;
  data?: any;
}

export interface FieldValidationResult {
  isValid: boolean;
  error?: string;
}

export class FormValidator {
  private schema: ZodSchema;
  private fieldSchemas: Record<string, ZodSchema> = {};

  constructor(schema: ZodSchema) {
    this.schema = schema;
    this.extractFieldSchemas();
  }

  validate(data: any): ValidationResult {
    try {
      const validatedData = this.schema.parse(data);
      return {
        success: true,
        errors: {},
        data: validatedData,
      };
    } catch (error) {
      if (error instanceof ZodError) {
        const errors: Record<string, string[]> = {};

        error.issues.forEach(issue => {
          const path = issue.path.join('.');
          if (!errors[path]) {
            errors[path] = [];
          }
          errors[path].push(issue.message);
        });

        return {
          success: false,
          errors,
        };
      }

      return {
        success: false,
        errors: { _root: ["Validation failed"] },
      };
    }
  }

  validateField(fieldName: string, value: any): FieldValidationResult {
    const fieldSchema = this.fieldSchemas[fieldName];
    if (!fieldSchema) {
      return { isValid: true };
    }

    try {
      fieldSchema.parse(value);
      return { isValid: true };
    } catch (error) {
      if (error instanceof ZodError) {
        const firstError = error.issues[0];
        return {
          isValid: false,
          error: firstError.message,
        };
      }

      return {
        isValid: false,
        error: "Validation failed",
      };
    }
  }

  private extractFieldSchemas(): void {
    if (this.schema instanceof z.ZodObject) {
      const shape = this.schema.shape;
      Object.keys(shape).forEach(key => {
        this.fieldSchemas[key] = shape[key];
      });
    }
  }

  static createValidator(schema: ZodSchema): FormValidator {
    return new FormValidator(schema);
  }
}

// Common validation schemas
export const CommonValidationSchemas = {
  email: z.string().email("Please enter a valid email address"),

  password: z.string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/[0-9]/, "Password must contain at least one number"),

  required: z.string().min(1, "This field is required"),

  optionalString: z.string().optional(),

  positiveNumber: z.number().positive("Must be a positive number"),

  uuid: z.string().uuid("Must be a valid UUID"),

  url: z.string().url("Must be a valid URL"),

  phoneNumber: z.string()
    .regex(/^[\+]?[1-9][\d]{0,15}$/, "Please enter a valid phone number"),

  leagueName: z.string()
    .min(2, "League name must be at least 2 characters")
    .max(50, "League name must be less than 50 characters"),

  teamName: z.string()
    .min(2, "Team name must be at least 2 characters")
    .max(30, "Team name must be less than 30 characters"),
};