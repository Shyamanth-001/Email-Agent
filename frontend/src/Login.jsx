import { GoogleLogin } from "@react-oauth/google";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Login({ onLogin }) {
  const handleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/google`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            credential: credentialResponse.credential,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Login failed");
      }

      const data = await response.json();

      localStorage.setItem(
        "access_token",
        data.access_token
      );

      onLogin(data.user);

    } catch (error) {
      console.error(error);
      alert("Google login failed");
    }
  };

  return (
    <div>
      <h2>Email Classifier</h2>

      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => {
          console.error("Google Login Failed");
        }}
      />
    </div>
  );
}

export default Login;