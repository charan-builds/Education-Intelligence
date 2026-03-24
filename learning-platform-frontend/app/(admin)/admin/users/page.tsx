"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { createUser, getUsers } from "@/services/userService";
import type { AssignableUserRole } from "@/types/user";

const ROLE_OPTIONS: AssignableUserRole[] = ["student", "teacher", "mentor", "admin"];

export default function AdminUsersPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AssignableUserRole>("student");

  const usersQuery = useQuery({
    queryKey: ["admin", "users"],
    queryFn: getUsers,
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => {
      toast({
        title: "User created",
        description: "The new tenant user has been persisted successfully.",
        variant: "success",
      });
      setEmail("");
      setPassword("");
      setRole("student");
      await queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: () => {
      toast({
        title: "User creation failed",
        description: "The backend rejected the request. Check the tenant role rules and password policy.",
        variant: "error",
      });
    },
  });

  const users = useMemo(
    () => (usersQuery.data?.items ?? []).filter((user) => user.email.toLowerCase().includes(search.toLowerCase())),
    [search, usersQuery.data?.items],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="User management"
        description="Create tenant users and review role distribution using `/users`."
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SurfaceCard title="Create user" description="Tenant-level user creation with password and role selection.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate({ email, password, role });
            }}
          >
            <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="user@tenant.com" type="email" required />
            <Input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Strong password" type="password" required />
            <Select value={role} onChange={(event) => setRole(event.target.value as AssignableUserRole)}>
              {ROLE_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create user"}
            </Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="User list" description="Search and browse the current tenant roster.">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Filter by email"
            className="mb-4"
          />
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Tenant</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3 text-slate-900 dark:text-slate-100">{user.email}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{user.role}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">#{user.tenant_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
