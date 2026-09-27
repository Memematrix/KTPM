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

export function logout() {
  localStorage.removeItem("access_token");
  currentUser = null;
  window.location.href = "/";
}
