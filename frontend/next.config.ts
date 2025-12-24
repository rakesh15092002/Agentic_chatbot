import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        // When the frontend calls /api/py/..., send it to FastAPI
        source: "/api/py/:path*",
        destination: "http://127.0.0.1:8000/:path*", 
        //added
      },
    ];
  },
};

export default nextConfig;
