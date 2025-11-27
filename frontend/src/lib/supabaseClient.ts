import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL!;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function uploadFileToSupabase(file: File) {
    // 1) Upload to Supabase Storage
    const fileName = `partner-${Date.now()}-${file.name.replace(/\s+/g, "_")}`;

    const { data, error } = await supabase.storage
        .from("biodata-images")                  // bucket name
        .upload(`profiles/${fileName}`, file, {
            cacheControl: "3600",
            upsert: false,
        });

    if (error || !data) {
        console.error("Supabase upload error:", error);
        return null;
    }

    // 2) Construct public URL
    return `${import.meta.env.VITE_SUPABASE_URL}/storage/v1/object/public/biodata-images/${data.path}`;
}