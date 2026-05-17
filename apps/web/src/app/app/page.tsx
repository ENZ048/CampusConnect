import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">Dashboard</h1>
      <Card>
        <CardHeader><CardTitle>Welcome to CampusConnect</CardTitle></CardHeader>
        <CardContent className="text-slate-600">
          Your dashboard is empty for now. Once you connect a WhatsApp number and a lead messages you,
          everything will show up here.
        </CardContent>
      </Card>
    </div>
  );
}
