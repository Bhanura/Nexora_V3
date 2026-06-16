import { Users, FileText, Server, ShieldAlert, HardDrive } from "lucide-react";
import { Card, CardContent } from "../ui/Card";

export default function SystemStats({ users }) {
  // Calculate stats on the frontend
  const totalUsers = users.length;
  const totalDocs = users.reduce((acc, user) => acc + (user.doc_count || 0), 0);
  const bannedUsers = users.filter(u => u.status === 'banned').length;
  const totalStorage = users.reduce((acc, user) => acc + (user.storage_mb || 0), 0);

  const stats = [
    { label: "Total Clients", value: totalUsers, icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Total Documents", value: totalDocs.toLocaleString(), icon: FileText, color: "text-purple-600", bg: "bg-purple-50" },
    { label: "Total Storage", value: `${totalStorage.toFixed(2)} MB`, icon: HardDrive, color: "text-orange-600", bg: "bg-orange-50" },
    { label: "Banned Users", value: bannedUsers, icon: ShieldAlert, color: "text-red-600", bg: "bg-red-50" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <Card key={i} className="border-none shadow-sm">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{stat.value}</p>
            </div>
            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} dark:bg-opacity-10`}>
              <stat.icon size={24} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}