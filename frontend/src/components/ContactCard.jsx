const ROLE_BADGE = {
  decision_maker: { label: "Decision Maker", color: "text-red-400 bg-red-900/30" },
  influencer: { label: "Influencer", color: "text-yellow-400 bg-yellow-900/30" },
  champion: { label: "Champion", color: "text-green-400 bg-green-900/30" },
};

export default function ContactCard({ contact, className = "" }) {
  const role = ROLE_BADGE[contact.role_type];

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-start gap-3 ${className}`}>
      <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-white font-bold flex-shrink-0">
        {contact.name?.[0] ?? "?"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white text-sm">{contact.name}</span>
          {role && (
            <span className={`text-xs px-1.5 py-0.5 rounded ${role.color}`}>{role.label}</span>
          )}
        </div>
        <p className="text-gray-400 text-xs">{contact.title}</p>
        {contact.functional_area && (
          <p className="text-gray-500 text-xs">{contact.functional_area}</p>
        )}
        {contact.recent_activity && (
          <p className="text-gray-500 text-xs mt-1 line-clamp-1 italic">Recent: {contact.recent_activity}</p>
        )}
        {contact.linkedin_url && (
          <a
            href={contact.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 text-xs hover:underline"
          >
            LinkedIn →
          </a>
        )}
      </div>
    </div>
  );
}
