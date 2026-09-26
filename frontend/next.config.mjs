/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.amazonaws.com" },
      { protocol: "https", hostname: "res.cloudinary.com" },
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "https", hostname: "via.placeholder.com" },
      { protocol: "https", hostname: "ui-avatars.com" },
    ],
  },
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version ?? "1.0.0",
  },
  webpack: (config) => {
    config.ignoreWarnings = [{ module: /node_modules\/@radix-ui/ }];
    return config;
  },
  async redirects() {
    return [
      { source: "/admin", destination: "/admin/dashboard", permanent: false },
      { source: "/parent", destination: "/parent/dashboard", permanent: false },
      { source: "/student", destination: "/student/dashboard", permanent: false },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
