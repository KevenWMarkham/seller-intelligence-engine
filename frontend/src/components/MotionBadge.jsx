const MOTION_STYLES = {
  wedge: { label: "WEDGE", color: "bg-orange-900/40 text-orange-400 border-orange-800" },
  new: { label: "NEW LOGO", color: "bg-blue-900/40 text-blue-400 border-blue-800" },
  expand: { label: "EXPAND", color: "bg-green-900/40 text-green-400 border-green-800" },
  displace: { label: "DISPLACE", color: "bg-red-900/40 text-red-400 border-red-800" },
};

export default function MotionBadge({ motion, className = "" }) {
  const style = MOTION_STYLES[motion] ?? { label: motion ?? "—", color: "bg-gray-800 text-gray-400 border-gray-700" };
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded border ${style.color} ${className}`}>
      {style.label}
    </span>
  );
}
