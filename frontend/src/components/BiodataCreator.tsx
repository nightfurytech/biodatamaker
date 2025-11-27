import React, {useRef, useState} from 'react';
import { Heart, Upload, Sparkles, ExternalLink } from 'lucide-react';
import imageCompression from 'browser-image-compression';
import {uploadFileToSupabase} from "@/lib/supabaseClient.ts";

interface FormData {
  name: string;
  dob: string;
  jobRole: string;
  location: string;
  socialMedia: string;
  aboutMe: string;
  partnerPreferences: string;
  image: File | null;
  imageUrl?: string;    // NEW
}

interface FormErrors {
  name?: string;
  dob?: string;
  jobRole?: string;
  location?: string;
  image?: string;
  aboutMe?: string;
  partnerPreferences?: string;
  submit?: string;
}

export default function BiodataCreator() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    dob: '',
    jobRole: '',
    location: '',
    socialMedia: '',
    aboutMe: '',
    partnerPreferences: '',
    image: null,
    imageUrl: ''
  });

  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [biodataUrl, setBiodataUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [showSizeError, setShowSizeError] = useState(false);

  const validateForm = () => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.dob) newErrors.dob = 'Date of birth is required';
    if (!formData.location.trim()) newErrors.location = 'Location is required';
    if (!formData.image) newErrors.image = 'Please upload your best photo';

    const aboutMeWords = formData.aboutMe.trim().split(/\s+/).filter(w => w.length > 0).length;
    if (aboutMeWords === 0 || aboutMeWords < 50) {
      newErrors.aboutMe = `About me must be exactly 50-250 words (current: ${aboutMeWords})`;
    } else if (aboutMeWords > 250) {
      newErrors.aboutMe = `About me must be exactly 50-250 words (current: ${aboutMeWords})`;
    }

    const prefWords = formData.partnerPreferences.trim().split(/\s+/).filter(w => w.length > 0).length;
    if (prefWords === 0 || prefWords < 50) {
      newErrors.partnerPreferences = `Partner preferences must be exactly 50-250 words (current: ${prefWords})`;
    } else if (prefWords > 250) {
      newErrors.partnerPreferences = `Partner preferences must be exactly 50-250 words (current: ${prefWords})`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateWordCount = (text: string, field: 'aboutMe' | 'partnerPreferences') => {
    const words = wordCount(text);
    if (words > 0 && (words < 50 || words > 250)) {
      setErrors(prev => ({
        ...prev,
        [field]: `Must be exactly 50-250 words (current: ${words})`
      }));
    } else {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset previous size error
    setShowSizeError(false);

    // 10 MB limit
    if (file.size > 10 * 1024 * 1024) {
      setShowSizeError(true);
      setErrors(prev => ({ ...prev, image: 'Please upload an image smaller than 10MB' }));

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    setLoading(true);

    try {
      // Optional: toast.info("Compressing image...");
      const options = {
        maxSizeMB: 0.5,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
      };

      // Compress image in browser
      const compressedFile = await imageCompression(file, options);

      // Upload compressed image to Supabase
      const imageUrl = await uploadFileToSupabase(compressedFile as File);
      if (!imageUrl) {
        console.error('Failed to upload image to Supabase');
        // toast.error('Failed to upload image');
        setErrors(prev => ({ ...prev, image: 'Failed to upload image. Please try again.' }));
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        setLoading(false);
        return;
      }

      // Preview compressed image
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
        // toast.success('Image ready!');
      };
      reader.readAsDataURL(compressedFile);

      // Optional: update the input to hold the compressed file
      const dataTransfer = new DataTransfer();
      const compressedFileAsFile = new File([compressedFile], file.name, {
        type: compressedFile.type,
      });
      dataTransfer.items.add(compressedFileAsFile);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
      }

      // Store file + URL in your form state
      setFormData(prev => ({
        ...prev,
        image: compressedFileAsFile,
        imageUrl: imageUrl,
      }));

      setErrors(prev => ({ ...prev, image: undefined }));
    } catch (error) {
      console.error('Compression / upload error:', error);
      // toast.error('Failed to process image');
      setErrors(prev => ({ ...prev, image: 'Failed to process image. Please try again.' }));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);

    try {
      const formDataToSend = new FormData();

      Object.keys(formData).forEach(key => {
        const value = formData[key as keyof FormData];

        if (key === "image") return; // ❌ Don't send file

        if (key === "imageUrl") {
          formDataToSend.append("image", value as string); // ✔ send URL as "image"
          return;
        }

        if (value !== null) {
          formDataToSend.append(key, String(value));
        }
      });


      const response = await fetch(`${import.meta.env.VITE_DOMAIN_URL || ''}/api/v1/generate-bio`, {
        method: 'POST',
        body: formDataToSend
      });

      const data = await response.json();

      if (data.url) {
        setBiodataUrl(data.url);
      }
    } catch (error) {
      setErrors({ submit: 'Failed to generate biodata. Please try again.' });
    } finally {
      setLoading(false);
    }
  };



  const wordCount = (text: string) => text.trim().split(/\s+/).filter(w => w.length > 0).length;

  if (biodataUrl) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-secondary via-muted to-secondary/50 flex items-center justify-center p-4 sm:p-6">
          <div className="bg-card rounded-3xl shadow-2xl p-6 sm:p-12 max-w-lg w-full text-center animate-fade-in">
            <div className="mb-6">
              <div className="w-20 h-20 bg-gradient-to-r from-primary to-love rounded-full flex items-center justify-center mx-auto mb-4 animate-heart-beat shadow-[var(--shadow-romantic)]">
                <Sparkles className="w-10 h-10 text-primary-foreground" />
              </div>
              <h2 className="text-3xl font-bold text-foreground mb-2">Your Biodata is Ready!</h2>
              <p className="text-muted-foreground">Share your profile with the world</p>
            </div>

            <div className="bg-gradient-to-r from-secondary to-muted rounded-2xl p-6 mb-6 border border-border">
              <p className="text-sm text-muted-foreground mb-3">Here you can find your biodata:</p>
              <div className="overflow-x-auto">
                <a
                    href={biodataUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-romantic font-medium whitespace-nowrap flex items-center justify-center gap-2 transition-colors"
                >
                  {biodataUrl}
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                </a>
              </div>
            </div>

            <button
                onClick={() => {
                  setBiodataUrl(null);
                  setFormData({
                    name: '',
                    dob: '',
                    jobRole: '',
                    location: '',
                    socialMedia: '',
                    aboutMe: '',
                    partnerPreferences: '',
                    image: null
                  });
                  setImagePreview(null);
                }}
                className="bg-gradient-to-r from-primary to-love text-primary-foreground px-8 py-3 rounded-full font-semibold hover:shadow-[var(--shadow-glow)] transition-all shadow-[var(--shadow-romantic)]"
            >
              Create Another Biodata
            </button>
          </div>
        </div>
    );
  }

  return (
      <div className="min-h-screen bg-gradient-to-br from-secondary via-muted to-secondary/50 py-6 sm:py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-6 sm:mb-8 animate-fade-in">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Heart className="w-8 h-8 sm:w-10 sm:h-10 text-primary fill-primary animate-heart-beat" />
              <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Create Your Biodata
              </h1>
            </div>
            <p className="text-muted-foreground text-base sm:text-lg">Find your perfect match with a beautiful profile</p>
          </div>

          <div className="bg-card rounded-2xl sm:rounded-3xl shadow-2xl p-4 sm:p-8 space-y-5 sm:space-y-6 border border-border">
            {/* Image Upload */}
            <div className="text-center">
              <label className="block mb-3 sm:mb-4">
              <span className="text-base sm:text-lg font-semibold text-foreground flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                Upload Your Best Photo
              </span>
              </label>
              <div className="relative">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                    id="image-upload"
                />
                <label
                    htmlFor="image-upload"
                    className="cursor-pointer block"
                >
                  {imagePreview ? (
                      <div className="relative w-32 h-32 sm:w-48 sm:h-48 mx-auto rounded-full overflow-hidden border-4 border-primary/20 shadow-[var(--shadow-romantic)] hover:border-primary/40 transition-all hover:scale-105 active:scale-95">
                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                      </div>
                  ) : (
                      <div className="w-32 h-32 sm:w-48 sm:h-48 mx-auto rounded-full border-4 border-dashed border-primary/30 flex flex-col items-center justify-center bg-secondary hover:bg-muted active:bg-muted transition-all animate-pulse-slow">
                        <Upload className="w-10 h-10 sm:w-12 sm:h-12 text-primary mb-2" />
                        <span className="text-sm sm:text-base text-primary font-medium">Click to upload</span>
                      </div>
                  )}
                </label>
              </div>
              {errors.image && <p className="text-destructive text-sm mt-2">{errors.image}</p>}
            </div>

            {/* Name */}
            <div>
              <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">Name *</label>
              <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 sm:px-4 py-3 sm:py-3.5 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="Your full name"
              />
              {errors.name && <p className="text-destructive text-sm mt-1">{errors.name}</p>}
            </div>

            {/* DOB & Job Role */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
              <div>
                <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">Date of Birth *</label>
                <input
                    type="date"
                    value={formData.dob}
                    onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                    className="w-full px-3 sm:px-4 py-3 sm:py-3.5 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
                {errors.dob && <p className="text-destructive text-sm mt-1">{errors.dob}</p>}
              </div>
              <div>
                <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">Job Role</label>
                <input
                    type="text"
                    value={formData.jobRole}
                    onChange={(e) => setFormData({ ...formData, jobRole: e.target.value })}
                    className="w-full px-3 sm:px-4 py-3 sm:py-3.5 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                    placeholder="Software Engineer"
                />
                {errors.jobRole && <p className="text-destructive text-sm mt-1">{errors.jobRole}</p>}
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">Current Location *</label>
              <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 sm:px-4 py-3 sm:py-3.5 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="Mumbai, India"
              />
              {errors.location && <p className="text-destructive text-sm mt-1">{errors.location}</p>}
            </div>

            {/* Social Media */}
            <div>
              <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">Social Media Handles</label>
              <div className="relative">
                <input
                    type="text"
                    value={formData.socialMedia}
                    onChange={(e) => setFormData({ ...formData, socialMedia: e.target.value })}
                    className="w-full px-3 sm:px-4 py-3 sm:py-3.5 rounded-xl border-2 border-input bg-background text-foreground text-sm sm:text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                    placeholder="Instagram:_amritadas_ LinkedIn:amrita-j-das"
                />
              </div>
            </div>

            {/* About Me */}
            <div>
              <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">
                About Me *
                <span className={`text-xs sm:text-sm ml-2 block sm:inline mt-1 sm:mt-0 ${
                    wordCount(formData.aboutMe) >= 50 && wordCount(formData.aboutMe) <= 250
                        ? 'text-green-600'
                        : 'text-destructive'
                }`}>
                ({wordCount(formData.aboutMe)} / 50-250 words)
              </span>
              </label>
              <textarea
                  value={formData.aboutMe}
                  onChange={(e) => {
                    setFormData({ ...formData, aboutMe: e.target.value });
                    validateWordCount(e.target.value, 'aboutMe');
                  }}
                  className="w-full px-3 sm:px-4 py-3 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all h-32 sm:h-36 resize-none"
                  placeholder="Tell us about yourself, your interests, hobbies, and what makes you unique..."
              />
              {errors.aboutMe && <p className="text-destructive text-sm mt-1 font-medium">{errors.aboutMe}</p>}
            </div>

            {/* Partner Preferences */}
            <div>
              <label className="block text-foreground font-semibold mb-2 text-sm sm:text-base">
                Partner Preferences *
                <span className={`text-xs sm:text-sm ml-2 block sm:inline mt-1 sm:mt-0 ${
                    wordCount(formData.partnerPreferences) >= 50 && wordCount(formData.partnerPreferences) <= 250
                        ? 'text-green-600'
                        : 'text-destructive'
                }`}>
                ({wordCount(formData.partnerPreferences)} / 50-250 words)
              </span>
              </label>
              <textarea
                  value={formData.partnerPreferences}
                  onChange={(e) => {
                    setFormData({ ...formData, partnerPreferences: e.target.value });
                    validateWordCount(e.target.value, 'partnerPreferences');
                  }}
                  className="w-full px-3 sm:px-4 py-3 rounded-xl border-2 border-input bg-background text-foreground text-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all h-32 sm:h-36 resize-none"
                  placeholder="Describe your ideal partner, their qualities, values, and what you're looking for in a relationship..."
              />
              {errors.partnerPreferences && <p className="text-destructive text-sm mt-1 font-medium">{errors.partnerPreferences}</p>}
            </div>

            {errors.submit && (
                <div className="bg-destructive/10 border-2 border-destructive/30 rounded-xl p-4 text-destructive text-center">
                  {errors.submit}
                </div>
            )}

            {/* Submit Button */}
            <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full bg-gradient-to-r from-primary to-love text-primary-foreground py-3.5 sm:py-4 rounded-xl font-bold text-base sm:text-lg hover:shadow-[var(--shadow-glow)] active:scale-98 transition-all shadow-[var(--shadow-romantic)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 touch-manipulation"
            >
              {loading ? (
                  <>
                    <div className="w-5 h-5 border-3 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                    Creating Your Biodata...
                  </>
              ) : (
                  <>
                    <Heart className="w-5 h-5 fill-primary-foreground" />
                    Generate My Biodata
                  </>
              )}
            </button>
          </div>
        </div>
      </div>
  );
}