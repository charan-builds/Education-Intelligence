import type { LucideIcon } from "lucide-react";

type LandingSectionHeadingProps = {
  badge: string;
  title: string;
  accent: string;
  description: string;
  icon: LucideIcon;
};

export default function LandingSectionHeading({
  badge,
  title,
  accent,
  description,
  icon: Icon,
}: LandingSectionHeadingProps) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <div className="inline-flex items-center gap-2 rounded-full border-2 border-yellow-200 bg-white/80 px-4 py-2 shadow-lg backdrop-blur-xl">
        <Icon className="h-4 w-4 text-yellow-600" />
        <span className="text-sm font-semibold text-slate-900">{badge}</span>
      </div>
      <h2 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
        {title} <span className="bg-gradient-to-r from-yellow-600 to-amber-600 bg-clip-text text-transparent">{accent}</span>
      </h2>
      <p className="mt-5 text-lg leading-8 text-slate-600">{description}</p>
    </div>
  );
}
