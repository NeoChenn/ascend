import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// A single shared Supabase client for the whole frontend.
// import { supabase } from '../supabaseClient' wherever you need it.
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
