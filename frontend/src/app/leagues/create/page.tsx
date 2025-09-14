"use client";

import React from "react";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_BASE } from "../../../services/client";
import { createLeague as apiCreateLeague } from "../../../services/api";
import { z } from "zod";
import { useEffect, useMemo } from "react";
import { Button } from "../../../components/ui/button";
import { Plus } from "lucide-react";
import { Input } from "../../../components/ui/input";
import { useToast } from "../../../components/ui/toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import OnboardingTour from "../../../components/OnboardingTour";

type LeagueCreate = {
  name: string;
  sport: string;
  league_type: string;
  season: string;
};

type LeagueResponse = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  invite_link?: string | null;
};

export default function CreateLeaguePage() {
  const router = useRouter();
  const toast = useToast();
  const [tourOpen, setTourOpen] = React.useState(false);
  const [formErrors, setFormErrors] = React.useState<string[]>([]);

  const schema = z.object({
    name: z.string().min(2, "Name must be at least 2 characters").max(200),
    sport: z.string().min(2, "Sport is required").max(50),
    league_type: z.string().min(2, "League type is required").max(50),
    season: z
      .string()
      .regex(/^\d{4}$/, "Season must be a 4-digit year")
      .refine((y) => Number(y) >= 2000 && Number(y) <= 3000, "Enter a valid year"),
  });

  type FormValues = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setFocus,
    setError,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "My League",
      sport: "nba",
      league_type: "redraft",
      season: new Date().getFullYear().toString(),
    },
    mode: "onBlur",
    reValidateMode: "onChange",
  });

  const createLeague = useMutation({
    mutationFn: async (data: LeagueCreate) => {
      return await apiCreateLeague(data);
    },
    onSuccess: (data) => {
      toast.show({ title: "League created", description: data.name });
      reset();
      setFormErrors([]);
      if (data.league_id) router.push(`/leagues/${data.league_id}`);
    },
    onError: (err: any) => {
      const status = err?.status as number | undefined;
      const details = err?.data?.detail as any;
      const collected: string[] = [];
      if (status === 422 && Array.isArray(details)) {
        for (const d of details) {
          const loc = Array.isArray(d?.loc) ? d.loc : [];
          const field = loc[1] as keyof FormValues | undefined;
          const msg = String(d?.msg || "Invalid value");
          if (
            field &&
            (["name", "sport", "league_type", "season"] as Array<keyof FormValues>).includes(field)
          ) {
            setError(field, { type: "server", message: msg });
          } else {
            collected.push(msg);
          }
        }
        setFormErrors(collected);
        // Focus first field-level error if any
        const first = Object.keys(errors)[0] as keyof FormValues | undefined;
        if (first) setFocus(first);
        toast.show({
          title: "Validation failed",
          description: "Please fix the highlighted fields.",
        });
      } else {
        toast.show({ title: "Failed to create league", description: String(err?.message || err) });
      }
    },
  });

  const onSubmit = handleSubmit((values) => {
    createLeague.mutate(values);
  });

  // Focus first invalid field on validation errors
  useEffect(() => {
    const first = Object.keys(errors)[0] as keyof FormValues | undefined;
    if (first) setFocus(first);
  }, [errors, setFocus]);

  const hasErrors = useMemo(() => Object.keys(errors).length > 0, [errors]);

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Create League</h1>
          <Button variant="ghost" onClick={() => setTourOpen(true)}>
            Start tour
          </Button>
        </div>

        <div className="rounded-md border p-4 space-y-4">
          <p className="text-xs text-gray-600">
            Uses Authorization: Bearer from localStorage key <code>uf_token</code>.
          </p>

          <form className="grid grid-cols-1 gap-4 sm:grid-cols-2" onSubmit={onSubmit} noValidate>
            {(hasErrors || formErrors.length > 0) && (
              <div
                className="col-span-full rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800"
                role="alert"
                aria-live="assertive"
              >
                <p className="font-medium">Please fix the following errors:</p>
                <ul className="list-inside list-disc">
                  {Object.entries(errors).map(([k, v]) => (
                    <li key={k}>{v?.message as string}</li>
                  ))}
                  {formErrors.map((m, i) => (
                    <li key={`form-${i}`}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
            <Input label="Name" {...register("name")} error={errors.name?.message} />
            <Input label="Sport" {...register("sport")} error={errors.sport?.message} />
            <Input
              label="League Type"
              {...register("league_type")}
              error={errors.league_type?.message}
            />
            <Input
              label="Season"
              inputMode="numeric"
              {...register("season")}
              error={errors.season?.message}
            />

            <div className="col-span-full flex items-center gap-2 pt-2">
              <Button
                data-tour="create-submit"
                type="submit"
                disabled={createLeague.isPending || isSubmitting}
                loading={createLeague.isPending || isSubmitting}
                leftIcon={<Plus className="h-4 w-4" aria-hidden />}
              >
                Create
              </Button>
              <span className="text-xs text-gray-600">API: {API_BASE || "/"} /leagues</span>
            </div>
          </form>

          {createLeague.isError && (
            <p className="text-sm text-red-600">{(createLeague.error as Error)?.message}</p>
          )}

          {/* Redirect occurs on success; no inline success block needed */}
        </div>

        <CreateLeagueTour open={tourOpen} onClose={() => setTourOpen(false)} />

        <Link className="text-blue-700 underline" href="/leagues">
          Back to Leagues
        </Link>
      </div>
    </main>
  );
}

// Onboarding tour steps for this page
function CreateLeagueTour({ open, onClose }: { open: boolean; onClose: () => void }) {
  const steps = [
    { selector: "#name", title: "League name", content: "Give your league a memorable name." },
    { selector: "#season", title: "Season", content: "Enter the 4-digit season year." },
    {
      selector: '[data-tour="create-submit"]',
      title: "Create",
      content: "Click Create to finish.",
    },
  ];
  return <OnboardingTour id="create-league" steps={steps} open={open} onClose={onClose} />;
}
