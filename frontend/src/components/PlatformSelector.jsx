import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPlatform, updatePlatform } from "../api/client";

const VENDOR_LABELS = {
  google: "Google Cloud",
  microsoft: "Microsoft",
  aws: "AWS",
  oracle: "Oracle",
  salesforce: "Salesforce",
  ibm: "IBM",
};

export default function PlatformSelector() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["platform"], queryFn: getPlatform });
  const mutation = useMutation({
    mutationFn: (vendor) => updatePlatform(vendor),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["platform"] }),
  });

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500">Platform:</span>
      <select
        className="bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded px-2 py-1"
        value={data?.active_vendor ?? ""}
        onChange={(e) => mutation.mutate(e.target.value)}
      >
        {(data?.supported_vendors ?? []).map((v) => (
          <option key={v} value={v}>{VENDOR_LABELS[v] ?? v}</option>
        ))}
      </select>
    </div>
  );
}
