import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://fqhoqakgrbctbnygfujr.supabase.co';
const supabaseKey = 'sb_publishable_ZcXrTyxcSnzJPpW8sVNwBw_ZlMrmGeD';

export const supabase = createClient(supabaseUrl, supabaseKey);
