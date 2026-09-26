"use client";

/**
 * New Student Registration — Multi-Step Form
 *
 * Steps:
 *  1. Personal Information
 *  2. Academic Information (class, admission date)
 *  3. Guardian Information
 *  4. Review & Submit
 *
 * Each step has its own Zod schema. Validation is run step-by-step
 * before allowing progression so the user gets immediate feedback.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { useCreateStudent } from "@/hooks/useStudents";
import { PageHeader } from "@/components/ui/PageHeader";
import { FormField } from "@/components/ui/FormField";
import { cn } from "@/lib/utils";

/* ══════════════════════════════════════════════════════════════════
   ZOD SCHEMAS
   ══════════════════════════════════════════════════════════════════ */

const personalInfoSchema = z.object({
  first_name: z.string().min(2, "First name must be at least 2 characters"),
  last_name: z.string().min(2, "Last name must be at least 2 characters"),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  gender: z.enum(["male", "female", "other"], {
    required_error: "Please select a gender",
  }),
  blood_group: z.string().optional(),
  address: z.string().min(5, "Address must be at least 5 characters"),
  medical_conditions: z.string().optional(),
});

const academicInfoSchema = z.object({
  admission_number: z.string().min(1, "Admission number is required"),
  current_class: z.string().min(1, "Class selection is required"),
  admission_date: z.string().min(1, "Admission date is required"),
});

const guardianInfoSchema = z.object({
  guardian_first_name: z.string().min(2, "Guardian first name is required"),
  guardian_last_name: z.string().min(2, "Guardian last name is required"),
  relationship: z.string().min(1, "Relationship is required"),
  guardian_phone: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .regex(/^[+\d\s()-]+$/, "Invalid phone format"),
  guardian_email: z.string().email("Invalid email").optional().or(z.literal("")),
  guardian_address: z.string().optional(),
  guardian_occupation: z.string().optional(),
});

// Combined schema (full form)
const fullStudentSchema = personalInfoSchema
  .merge(academicInfoSchema)
  .merge(guardianInfoSchema);

type FullStudentFormValues = z.infer<typeof fullStudentSchema>;

/* ══════════════════════════════════════════════════════════════════
   STEP CONFIG
   ══════════════════════════════════════════════════════════════════ */
const STEPS = [
  { id: 1, label: "Personal Info", schema: personalInfoSchema },
  { id: 2, label: "Academic Info", schema: academicInfoSchema },
  { id: 3, label: "Guardian Info", schema: guardianInfoSchema },
  { id: 4, label: "Review & Submit", schema: null },
];

/* ══════════════════════════════════════════════════════════════════
   STEP INDICATORS
   ══════════════════════════════════════════════════════════════════ */
function StepIndicator({ currentStep }: { currentStep: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {STEPS.map((step, index) => {
        const isDone = currentStep > step.id;
        const isActive = currentStep === step.id;

        return (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition-colors",
                  isDone && "bg-secondary-600 text-white",
                  isActive && "bg-primary-700 text-white",
                  !isDone && !isActive && "bg-gray-100 text-gray-400",
                )}
              >
                {isDone ? <Check className="h-4 w-4" /> : step.id}
              </div>
              <span
                className={cn(
                  "hidden text-xs font-medium sm:block",
                  isActive ? "text-primary-700" : isDone ? "text-secondary-600" : "text-gray-400",
                )}
              >
                {step.label}
              </span>
            </div>
            {index < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-2 h-0.5 w-8 sm:w-16 transition-colors",
                  isDone ? "bg-secondary-400" : "bg-gray-200",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════
   PAGE COMPONENT
   ══════════════════════════════════════════════════════════════════ */
export default function NewStudentPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const createStudent = useCreateStudent();

  const methods = useForm<FullStudentFormValues>({
    resolver: zodResolver(fullStudentSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      date_of_birth: "",
      gender: "male",
      blood_group: "",
      address: "",
      medical_conditions: "",
      admission_number: "",
      current_class: "",
      admission_date: new Date().toISOString().split("T")[0],
      guardian_first_name: "",
      guardian_last_name: "",
      relationship: "Father",
      guardian_phone: "",
      guardian_email: "",
      guardian_address: "",
      guardian_occupation: "",
    },
    mode: "onChange",
  });

  const { getValues, trigger, formState: { isSubmitting } } = methods;

  /* Validate current step fields before proceeding */
  const handleNext = async () => {
    const stepSchema = STEPS[currentStep - 1].schema;
    if (!stepSchema) { setCurrentStep((s) => s + 1); return; }

    const fieldNames = Object.keys(stepSchema.shape) as (keyof FullStudentFormValues)[];
    const valid = await trigger(fieldNames);
    if (valid) setCurrentStep((s) => s + 1);
  };

  const handleBack = () => setCurrentStep((s) => Math.max(1, s - 1));

  const onSubmit = async (values: FullStudentFormValues) => {
    const payload = {
      first_name: values.first_name,
      last_name: values.last_name,
      date_of_birth: values.date_of_birth,
      gender: values.gender,
      blood_group: values.blood_group || undefined,
      address: values.address,
      medical_conditions: values.medical_conditions || undefined,
      admission_number: values.admission_number,
      current_class: values.current_class,
      admission_date: values.admission_date,
      guardians: [
        {
          first_name: values.guardian_first_name,
          last_name: values.guardian_last_name,
          relationship: values.relationship,
          phone: values.guardian_phone,
          email: values.guardian_email || undefined,
          address: values.guardian_address || undefined,
          occupation: values.guardian_occupation || undefined,
          is_primary: true,
        },
      ],
    };

    try {
      await createStudent.mutateAsync(payload as never);
      toast.success("Student registered successfully!");
      router.push("/admin/students");
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? "Failed to register student.");
    }
  };

  const values = getValues();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
        <PageHeader title="Register New Student" subtitle="Fill in all required fields" />
      </div>

      <div className="mx-auto max-w-2xl">
        <StepIndicator currentStep={currentStep} />

        <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-card">
          <FormProvider {...methods}>
            <form onSubmit={methods.handleSubmit(onSubmit)}>

              {/* ── STEP 1: Personal Info ─────────────────────── */}
              {currentStep === 1 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Personal Information</h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField name="first_name" label="First Name" placeholder="e.g. Kwame" required />
                    <FormField name="last_name" label="Last Name" placeholder="e.g. Asante" required />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField name="date_of_birth" label="Date of Birth" type="date" required />
                    <FormField name="gender" label="Gender" type="select" required
                      options={[
                        { value: "male", label: "Male" },
                        { value: "female", label: "Female" },
                        { value: "other", label: "Other" },
                      ]}
                    />
                  </div>
                  <FormField name="blood_group" label="Blood Group" type="select"
                    options={["A+","A-","B+","B-","AB+","AB-","O+","O-"].map((g) => ({ value: g, label: g }))}
                  />
                  <FormField name="address" label="Home Address" placeholder="Full residential address" required />
                  <FormField name="medical_conditions" label="Medical Conditions" placeholder="Any allergies, chronic conditions, or medications (optional)" />
                </div>
              )}

              {/* ── STEP 2: Academic Info ─────────────────────── */}
              {currentStep === 2 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Academic Information</h3>
                  <FormField name="admission_number" label="Admission Number" placeholder="e.g. STU-2025-001" required />
                  <FormField name="current_class" label="Class" type="select" required
                    placeholder="Select a class"
                    options={[
                      { value: "", label: "— Select class —" },
                      { value: "grade-1", label: "Grade 1" },
                      { value: "grade-2", label: "Grade 2" },
                      { value: "grade-3", label: "Grade 3" },
                      { value: "grade-4", label: "Grade 4" },
                      { value: "grade-5", label: "Grade 5" },
                      { value: "grade-6", label: "Grade 6" },
                    ]}
                  />
                  <FormField name="admission_date" label="Admission Date" type="date" required />
                </div>
              )}

              {/* ── STEP 3: Guardian Info ─────────────────────── */}
              {currentStep === 3 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Primary Guardian Information</h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField name="guardian_first_name" label="First Name" placeholder="Guardian's first name" required />
                    <FormField name="guardian_last_name" label="Last Name" placeholder="Guardian's last name" required />
                  </div>
                  <FormField name="relationship" label="Relationship to Student" type="select" required
                    options={["Father","Mother","Guardian","Uncle","Aunt","Grandparent","Sibling","Other"].map((r) => ({ value: r, label: r }))}
                  />
                  <FormField name="guardian_phone" label="Phone Number" type="tel" placeholder="+233 XX XXX XXXX" required />
                  <FormField name="guardian_email" label="Email Address" type="email" placeholder="guardian@email.com (optional)" />
                  <FormField name="guardian_occupation" label="Occupation" placeholder="Optional" />
                  <FormField name="guardian_address" label="Address (if different)" placeholder="Optional" />
                </div>
              )}

              {/* ── STEP 4: Review ────────────────────────────── */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Review & Submit</h3>

                  {/* Personal */}
                  <div className="rounded-lg bg-gray-50 p-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Personal</h4>
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <dt className="text-gray-500">Name</dt>
                      <dd className="text-gray-900 font-medium">{values.first_name} {values.last_name}</dd>
                      <dt className="text-gray-500">DOB</dt>
                      <dd className="text-gray-900">{values.date_of_birth}</dd>
                      <dt className="text-gray-500">Gender</dt>
                      <dd className="text-gray-900 capitalize">{values.gender}</dd>
                    </dl>
                  </div>

                  {/* Academic */}
                  <div className="rounded-lg bg-gray-50 p-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Academic</h4>
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <dt className="text-gray-500">Admission No.</dt>
                      <dd className="text-gray-900 font-mono">{values.admission_number}</dd>
                      <dt className="text-gray-500">Class</dt>
                      <dd className="text-gray-900">{values.current_class}</dd>
                      <dt className="text-gray-500">Admitted</dt>
                      <dd className="text-gray-900">{values.admission_date}</dd>
                    </dl>
                  </div>

                  {/* Guardian */}
                  <div className="rounded-lg bg-gray-50 p-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Guardian</h4>
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <dt className="text-gray-500">Name</dt>
                      <dd className="text-gray-900">{values.guardian_first_name} {values.guardian_last_name}</dd>
                      <dt className="text-gray-500">Relationship</dt>
                      <dd className="text-gray-900">{values.relationship}</dd>
                      <dt className="text-gray-500">Phone</dt>
                      <dd className="text-gray-900">{values.guardian_phone}</dd>
                    </dl>
                  </div>
                </div>
              )}

              {/* ── Navigation buttons ────────────────────────── */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
                <button
                  type="button"
                  onClick={handleBack}
                  disabled={currentStep === 1}
                  className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Previous
                </button>

                {currentStep < 4 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-800 transition-colors"
                  >
                    Next
                    <ArrowRight className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={isSubmitting || createStudent.isPending}
                    className={cn(
                      "flex items-center gap-2 rounded-lg px-6 py-2 text-sm font-semibold text-white transition-colors",
                      "bg-secondary-600 hover:bg-secondary-700",
                      (isSubmitting || createStudent.isPending) && "opacity-70 cursor-not-allowed",
                    )}
                  >
                    {(isSubmitting || createStudent.isPending) ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Registering…
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4" />
                        Register Student
                      </>
                    )}
                  </button>
                )}
              </div>
            </form>
          </FormProvider>
        </div>

        {/* Progress indicator */}
        <p className="mt-4 text-center text-xs text-gray-400">
          Step {currentStep} of {STEPS.length}
        </p>
      </div>
    </div>
  );
}
