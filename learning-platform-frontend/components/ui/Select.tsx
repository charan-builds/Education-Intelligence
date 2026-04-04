"use client";

import React from "react";

import { cn } from "@/utils/cn";

type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

export default function Select({ className, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "field-control",
        className,
      )}
      {...props}
    />
  );
}
