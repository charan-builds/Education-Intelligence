"use client";

export const dynamic = "force-dynamic";

import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createUser, getUsers } from "@/services/userService";
import type { UserRole } from "@/types/user";

const ROLE_OPTIONS: UserRole[] = ["student", "teacher", "admin", "super_admin"];

export default function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [formError, setFormError] = useState("");

  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: getUsers,
  });

  const createUserMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => {
      setEmail("");
      setPassword("");
      setRole("student");
      setFormError("");
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: () => {
      setFormError("Failed to create user.");
    },
  });

  const users = useMemo(() => usersQuery.data?.items ?? [], [usersQuery.data?.items]);

  const analytics = useMemo(() => {
    const byRole: Record<UserRole, number> = {
      student: 0,
      teacher: 0,
      admin: 0,
      super_admin: 0,
    };

    for (const user of users) {
      byRole[user.role] += 1;
    }

    return {
      totalUsers: users.length,
      roleDistribution: byRole,
    };
  }, [users]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");

    if (!email || !password) {
      setFormError("Email and password are required.");
      return;
    }

    await createUserMutation.mutateAsync({
      email,
      password,
      role,
    });
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Admin Dashboard</h1>
      <p className="mt-2 text-slate-600">Manage tenant users and monitor user analytics.</p>

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <p className="text-sm text-slate-500">Total Users</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{analytics.totalUsers}</p>
        </article>

        {ROLE_OPTIONS.map((roleName) => (
          <article key={roleName} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm capitalize text-slate-500">{roleName.replace("_", " ")}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{analytics.roleDistribution[roleName]}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Create User</h2>
        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="role">
              Role
            </label>
            <select
              id="role"
              value={role}
              onChange={(event) => setRole(event.target.value as UserRole)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {ROLE_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={createUserMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {createUserMutation.isPending ? "Creating..." : "Create User"}
            </button>
          </div>
        </form>

        {formError && <p className="mt-3 text-sm text-red-600">{formError}</p>}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Users</h2>

        {usersQuery.isLoading && <p className="mt-4 text-slate-600">Loading users...</p>}
        {usersQuery.isError && <p className="mt-4 text-red-600">Failed to load users.</p>}

        {!usersQuery.isLoading && !usersQuery.isError && users.length === 0 && (
          <p className="mt-4 text-slate-600">No users found.</p>
        )}

        {users.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3">{user.id}</td>
                    <td className="px-4 py-3">{user.email}</td>
                    <td className="px-4 py-3 capitalize">{user.role.replace("_", " ")}</td>
                    <td className="px-4 py-3">{new Date(user.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
