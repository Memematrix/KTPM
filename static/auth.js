let currentUser = null;
let fetchPromise = null;

export function getCachedUser() {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
}

export async function getCurrentUser() {
  if (currentUser) {
    return currentUser;
  }

  if (fetchPromise) {
    //prevent dup api calls
    return fetchPromise;
  }

  const token = localStorage.getItem("access_token");
  if (!token) {
    return null;
  }
  fetchPromise = (async () => {
    try {
      const res = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        currentUser = await res.json();

        localStorage.setItem("user", JSON.stringify(currentUser));
        return currentUser;
      }

      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      return null;
    } catch (error) {
      console.error("Error fetching current user:", error);
      return null;
    } finally {
      fetchPromise = null; //close api call
    }
  })();
  return fetchPromise; //should be null at this point
}

export async function logout() {
  try {
    const res = await fetch("/api/auth/logout", { method: "POST" });
    if (!res.ok) {
      throw new Error("Could not log out");
    }
  } catch (error) {
    console.error("Error logging out:", error);
    alert("Could not log out. Please try again.");
    return;
  }
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  currentUser = null;
  window.location.href = "/";
}
