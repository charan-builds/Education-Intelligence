"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useAuth } from "@/hooks/useAuth";
import { disableMfa, enableMfa, setupMfa } from "@/services/authService";
import { completeMyProfile, getMyProfile, updateMyProfile } from "@/services/userService";
import { getRoleHomePath } from "@/utils/appRoutes";

export default function StudentProfilePage() {
  const router = useRouter();
  const { refresh, role } = useAuth();
  const isIndependentLearner = role === "independent_learner";
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const profileQuery = useQuery({
    queryKey: ["student", "profile"],
    queryFn: getMyProfile,
  });
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [preferences, setPreferences] = useState('{\n  "theme": "adaptive",\n  "study_reminders": true\n}');
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const workspaceLabel = isIndependentLearner ? "independent learner workspace" : "student workspace";
  const onboardingDescription = isIndependentLearner
    ? "Complete your required onboarding details, then personalize your self-directed learning profile and secure your account with authenticator-based MFA."
    : "Complete your required onboarding details, then personalize your profile and secure your account with authenticator-based MFA.";
  const completionUnlockDescription = isIndependentLearner
    ? "Goal selection, diagnostics, roadmap, and progress tracking unlock after this first-time onboarding step."
    : "Diagnostic, roadmap, and dashboard access unlock after this first-time onboarding step.";
  const onboardingOrganizationPlaceholder = isIndependentLearner
    ? "Learning organization or community (optional)"
    : "College or institution (optional)";
  const profileCardDescription = isIndependentLearner
    ? "These fields are stored in the platform API and reused across your independent learner workspace."
    : "These fields are stored in the platform API and reused across the student workspace.";
  const profileOrganizationPlaceholder = isIndependentLearner
    ? "Learning organization, company, or community"
    : "College name";

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }
    setFullName(profileQuery.data.full_name ?? "");
    setPhoneNumber(profileQuery.data.phone_number ?? "");
    setLinkedinUrl(profileQuery.data.linkedin_url ?? "");
    setOrganizationName(profileQuery.data.organization_name ?? profileQuery.data.college_name ?? "");
    setDisplayName(profileQuery.data.display_name ?? "");
    setAvatarUrl(profileQuery.data.avatar_url ?? "");
    setPreferences(JSON.stringify(profileQuery.data.preferences ?? {}, null, 2));
  }, [profileQuery.data]);

  const profileMutation = useMutation({
    mutationFn: updateMyProfile,
    onSuccess: async () => {
      toast({ title: "Profile updated", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error: Error) => {
      toast({ title: "Profile update failed", description: error.message, variant: "error" });
    },
  });

  const completeProfileMutation = useMutation({
    mutationFn: completeMyProfile,
    onSuccess: async () => {
      toast({ title: "Profile completed", description: `You now have full access to the ${workspaceLabel}.`, variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
      await refresh();
      router.replace(getRoleHomePath(role));
    },
    onError: (error: Error) => {
      toast({ title: "Profile completion failed", description: error.message, variant: "error" });
    },
  });

  const setupMfaMutation = useMutation({
    mutationFn: setupMfa,
    onSuccess: (payload) => {
      setMfaSecret(payload.manual_entry_code);
      toast({ title: "MFA secret generated", description: "Add it to your authenticator app, then confirm with a 6-digit code.", variant: "success" });
    },
    onError: (error: Error) => {
      toast({ title: "MFA setup failed", description: error.message, variant: "error" });
    },
  });

  const enableMfaMutation = useMutation({
    mutationFn: enableMfa,
    onSuccess: async () => {
      toast({ title: "MFA enabled", variant: "success" });
      setMfaCode("");
      await queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
    },
    onError: (error: Error) => {
      toast({ title: "MFA enable failed", description: error.message, variant: "error" });
    },
  });

  const disableMfaMutation = useMutation({
    mutationFn: disableMfa,
    onSuccess: async () => {
      toast({ title: "MFA disabled", description: "Your active sessions were rotated for safety.", variant: "success" });
      setMfaSecret("");
      setMfaCode("");
      await queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
    },
    onError: (error: Error) => {
      toast({ title: "MFA disable failed", description: error.message, variant: "error" });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Profile"
        title="Manage your learning identity"
        description={onboardingDescription}
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        {!profileQuery.data?.is_profile_completed ? (
          <SurfaceCard
            title="Complete your profile"
            description={completionUnlockDescription}
          >
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                completeProfileMutation.mutate({
                  full_name: fullName,
                  phone_number: phoneNumber,
                  linkedin_url: linkedinUrl,
                  organization_name: organizationName || null,
                });
              }}
            >
              <Input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
              <Input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} placeholder="+14155550123" />
              <Input value={linkedinUrl} onChange={(event) => setLinkedinUrl(event.target.value)} placeholder="https://www.linkedin.com/in/your-profile/" />
              <Input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} placeholder={onboardingOrganizationPlaceholder} />
              <Button type="submit" disabled={completeProfileMutation.isPending}>
                {completeProfileMutation.isPending ? "Completing..." : "Complete profile"}
              </Button>
            </form>
          </SurfaceCard>
        ) : null}

        <SurfaceCard title="Profile" description={profileCardDescription}>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              let parsedPreferences: Record<string, unknown> = {};
              try {
                parsedPreferences = preferences.trim() ? JSON.parse(preferences) : {};
              } catch {
                toast({ title: "Invalid preferences JSON", description: "Fix the JSON block before saving.", variant: "error" });
                return;
              }
              profileMutation.mutate({
                full_name: fullName || null,
                display_name: displayName || null,
                phone_number: phoneNumber || null,
                linkedin_url: linkedinUrl || null,
                organization_name: organizationName || null,
                avatar_url: avatarUrl || null,
                preferences: parsedPreferences,
              });
            }}
          >
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
            <Input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Display name" />
            <Input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} placeholder="Phone number" />
            <Input value={linkedinUrl} onChange={(event) => setLinkedinUrl(event.target.value)} placeholder="LinkedIn URL" />
            <Input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} placeholder={profileOrganizationPlaceholder} />
            <Input value={avatarUrl} onChange={(event) => setAvatarUrl(event.target.value)} placeholder="Avatar URL" />
            <textarea
              value={preferences}
              onChange={(event) => setPreferences(event.target.value)}
              rows={8}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
            <Button type="submit" disabled={profileMutation.isPending}>
              {profileMutation.isPending ? "Saving..." : "Save profile"}
            </Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Security" description="Authenticator-based MFA is enforced at login once enabled.">
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Account</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{profileQuery.data?.email ?? "Loading..."}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                {profileQuery.data?.mfa_enabled ? "MFA enabled" : "MFA not enabled"}
              </p>
            </div>

            {!profileQuery.data?.mfa_enabled ? (
              <>
                <Button onClick={() => setupMfaMutation.mutate()} disabled={setupMfaMutation.isPending}>
                  {setupMfaMutation.isPending ? "Generating..." : "Generate MFA secret"}
                </Button>
                {mfaSecret ? (
                  <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-100">
                    Authenticator secret: <span className="font-semibold">{mfaSecret}</span>
                  </div>
                ) : null}
                <Input value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} placeholder="Enter 6-digit MFA code" />
                <Button
                  variant="secondary"
                  onClick={() => enableMfaMutation.mutate(mfaCode)}
                  disabled={!mfaCode.trim() || enableMfaMutation.isPending}
                >
                  {enableMfaMutation.isPending ? "Enabling..." : "Enable MFA"}
                </Button>
              </>
            ) : (
              <>
                <Input value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} placeholder="Enter current 6-digit MFA code" />
                <Button
                  variant="ghost"
                  onClick={() => disableMfaMutation.mutate(mfaCode)}
                  disabled={!mfaCode.trim() || disableMfaMutation.isPending}
                >
                  {disableMfaMutation.isPending ? "Disabling..." : "Disable MFA"}
                </Button>
              </>
            )}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
