import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../supabaseClient'

// AuthContext gives any component access to the current user and signOut function.
// useAuth() is the hook components use to read from this context.
const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // loading stays true until the initial session check completes — prevents a
  // flash where the app renders as "logged out" before Supabase has checked localStorage.
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check whether a session already exists (e.g. page refresh with a stored token)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Subscribe to future changes: login, logout, token refresh
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    //A feature specific to useEffect. optionally return a cleanup function, and React calls that function when the component unmounts.
    return () => subscription.unsubscribe() 
  }, [])

  const signOut = () => supabase.auth.signOut()

  return (
    <AuthContext.Provider value={{ user, signOut }}>
      {!loading && children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
