export async function GET() {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/api/analytics",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            return Response.json(
                { error: "Backend analytics API failed" },
                { status: response.status }
            );
        }

        const data = await response.json();

        return Response.json(data);
    } catch (error) {
        console.error("Analytics API error:", error);

        return Response.json(
            { error: "Unable to connect to analytics backend" },
            { status: 500 }
        );
    }
}
