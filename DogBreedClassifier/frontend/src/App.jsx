import axios from "axios";
import { useMutation } from "@tanstack/react-query";
import { useState, useEffect } from "react";

/* ----------------------------------------------------------------------------
   PawID – Dog-breed identifier (React + Tailwind)
---------------------------------------------------------------------------- */
const canon = (s) =>
  s
    .replace(/[_-]/g, " ")
    .replace(/[()]/g, " ")
    .replace(/\bdog$/i, "")
    .replace(/\s+/g, " ")
    .trim();

    

const clean = (s) => s.replace(/\s*\(.*?\)\s*$/, "").trim();


const emotionEmoji = {
  angry:   "😠",
  happy:   "😄",
  relaxed: "😌",
  sad:     "😢",
};


const Spinner = () => (
  <div className="flex justify-center py-12">
    <svg
      className="animate-spin h-12 w-12 text-indigo-600"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8h8a8 8 0 11-16 0z"
      />
    </svg>
  </div>
);

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // ➞ now calls BOTH endpoints in parallel:
  const predict = useMutation({
    mutationFn: async (form) => {
      const [breedRes, emoRes] = await Promise.all([
        axios.post(`${import.meta.env.VITE_API}/predict`, form),
        axios.post(`${import.meta.env.VITE_API}/predict_emotion`, form),
      ]);
      return {
        ...breedRes.data,
        emotion: emoRes.data,     // attach emotion under `.emotion`
      };
    },
  });

  useEffect(() => {
    if (predict.isSuccess) {
      console.log("Top-3 breeds:", predict.data.labels, predict.data.probs);
      console.log("Top-3 emotions:", predict.data.emotion.labels, predict.data.emotion.probs);
    }
  }, [predict.isSuccess]);

  const handleUpload = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const allowed = ["image/png", "image/jpeg", "image/gif"];
    if (!allowed.includes(f.type)) {
      setErrorMessage("Unsupported format. Please upload PNG, JPG, or GIF.");
      setFile(null);
      setPreview(null);
      predict.reset();
      return;
    }
    setErrorMessage("");
    setFile(f);
    setPreview(URL.createObjectURL(f));
    predict.reset();
  };

  const handleSubmit = () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    predict.mutate(form);
  };

  return (
    <div className="bg-white min-h-screen font-sans text-gray-800">
      {/* Header */}
      <div className="py-10">
        <header className="mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Identify Your Dog's Breed
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Upload a photo of your dog and discover their breed, characteristics,
            care information—and now their mood!
          </p>
        </header>

        {/* Main */}
        <main className="mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
          <UploadCard
            preview={preview}
            handleUpload={handleUpload}
            handleSubmit={handleSubmit}
            isLoading={predict.isLoading}
            disabled={!file}
          />

          {errorMessage && (
            <p className="mt-2 text-sm text-red-600">{errorMessage}</p>
          )}

          {predict.isLoading && <Spinner />}

          {predict.isSuccess && !predict.isLoading && (
            <>
              <ResultsCard
                data={predict.data}
                preview={preview}
                onReset={() => {
                  setFile(null);
                  setPreview(null);
                  predict.reset();
                  setErrorMessage("");
                }}
              />
              <SimilarBreeds labels={predict.data.labels} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}


/* ----------------------------------------------------------------------------
   UploadCard
---------------------------------------------------------------------------- */
function UploadCard({ preview, handleUpload, handleSubmit, isLoading, disabled }) {
  return (
    <div className="mt-8 mb-12">
      <div className="bg-indigo-50 rounded-lg overflow-hidden shadow divide-y divide-gray-200">
        <div className="px-4 py-5 sm:px-6">
          <p className="text-lg font-medium text-gray-900">Upload Your Dog's Photo</p>
          <p className="mt-1 text-sm text-gray-600">
            Clear photos will provide the most accurate results
          </p>
        </div>
        <div className="px-4 py-8 sm:px-6">
          <div className="space-y-6">
            <div className="flex justify-center">
              <div className="w-full max-w-lg">
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 rounded-md border-2 border-dashed border-gray-300">
                  <div className="text-center space-y-4">
                    <div className="mx-auto flex h-24 w-24 items-center justify-center">
                      <img
                        alt="Dog upload icon"
                        src={preview || "https://placehold.co/150x150?text=Dog+Photo"}
                        className="h-24 w-24 object-contain rounded"
                      />
                    </div>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer rounded-md bg-white font-medium text-indigo-600 hover:text-indigo-500"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          type="file"
                          className="sr-only"
                          onChange={handleUpload}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <button
                onClick={handleSubmit}
                disabled={disabled || isLoading}
                className="inline-flex justify-center rounded-md border border-indigo-500 bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 hover:bg-indigo-700 disabled:opacity-50"
              >
                {isLoading ? "Identifying…" : "Identify Breed"}  
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


/* ----------------------------------------------------------------------------
   Detail & MetricBar helpers
---------------------------------------------------------------------------- */
const Detail = ({ title, value }) => (
  <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
    <dt className="text-sm font-medium text-gray-500">{title}</dt>
    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{value}</dd>
  </div>
);

const MetricBar = ({ label, value }) => (
  <div className="my-3">
    <div className="flex justify-between text-sm font-medium">
      <span>{label}</span>
      <span>{value}/5</span>
    </div>
    <div className="w-full bg-gray-200 h-2 rounded-full">
      <div
        className="h-2 rounded-full bg-indigo-600"
        style={{ width: `${(value / 5) * 100}%` }}
      />
    </div>
  </div>
);

/* ----------------------------------------------------------------------------
   Emoji map for emotions
---------------------------------------------------------------------------- */


/* ----------------------------------------------------------------------------
   ResultsCard – with separate Emotion panel beneath the Breed section
---------------------------------------------------------------------------- */
const ResultsCard = ({ data, preview, onReset }) => {
  // ── BREED DATA ─────────────────────────────────────────────────────────────
  const dogInfo     = data.info?.thedogapi || {};
  const ninjaInfo   = data.info?.api_ninjas || {};
  const pick        = (a,b,f="n/a") => a ?? b ?? f;
  const breedName   = pick(dogInfo.name, ninjaInfo.name, data.top);
  const temperament = pick(dogInfo.temperament, ninjaInfo.temperament, "")
                        .split(/,\s*/).filter(Boolean).slice(0,3);
  const imageSrc    = data.image_url || ninjaInfo.image_link || preview;
  const topProb     = (data.probs[0] * 100).toFixed(0);

  // ── EMOTION DATA ────────────────────────────────────────────────────────────
  const { top: emoTop, probs: emoProbs, labels: emoLabels } = data.emotion;
  const topThree = emoLabels
  .map((lbl, i) => ({ lbl, pct: (emoProbs[i] * 100).toFixed(0) }))
  .slice(0, 3);

  return (
    <div className="mt-10 bg-white rounded-lg overflow-hidden shadow">
      {/* Header */}
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <p className="text-lg font-medium text-gray-900">Results</p>
        <p className="mt-1 text-sm text-gray-500">Identified based on your image</p>
      </div>

      {/* Main grid */}
      <div className="px-4 py-5 sm:p-6 md:grid md:grid-cols-3 md:gap-6">
        {/* ── LEFT COLUMN: Breed + Mood ── */}
        <div className="md:col-span-1 space-y-6">
            {/* — re-added dog photo — */}
            {imageSrc && (
              <img
              src={imageSrc}
              alt={breedName}
              className="w-full h-auto object-cover rounded-lg"
              />
              )}
          {/* Breed panel */}
          <div className="bg-indigo-50 rounded-md p-4">
            <p className="text-center text-lg font-semibold text-gray-800">
              {breedName}
            </p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              {temperament.map(t => (
                <span
                  key={t}
                  className="px-2.5 py-0.5 bg-indigo-100 text-indigo-800 text-xs font-medium rounded-full"
                >
                  {t}
                </span>
              ))}
            </div>
            <div className="mt-4">
              <Detail title="Confidence" value={`${topProb}%`} />
              <div className="mt-1 w-full bg-gray-200 h-2 rounded-full">
                <div
                  className="h-2 rounded-full bg-indigo-600"
                  style={{ width: `${topProb}%` }}
                />
              </div>
            </div>
          </div>

          {/* Mood panel (directly under breed) */}
          <div className="bg-green-50 rounded-md p-4">
            <p className="text-center text-lg font-semibold text-green-800">
              Mood
            </p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
            {topThree.map(({ lbl, pct }, idx) => {
                const cap = lbl.charAt(0).toUpperCase() + lbl.slice(1);
                const badgeClasses =
                  idx === 0
                    ? "px-3 py-1 bg-green-200 text-green-900 text-xs font-semibold rounded-full ring-2 ring-green-400"
                    : "px-2.5 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded-full";
                return (
                  <span key={lbl} className={badgeClasses}>
                    {cap} {emotionEmoji[lbl]} — {pct}%
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Stats & Ratings ── */}
        <div className="mt-5 md:mt-0 md:col-span-2">
          <dl className="divide-y divide-gray-200">
            <Detail title="Breed Group" value={pick(dogInfo.breed_group, ninjaInfo.group)} />
            <Detail
              title="Size"
              value={pick(
                `${dogInfo.height?.imperial||"-"}in, ${dogInfo.weight?.imperial||"-"}lbs`,
                `${ninjaInfo.min_height_male||ninjaInfo.min_height_female||"-"}–${ninjaInfo.max_height_male||ninjaInfo.max_height_female||"-"}in, ${ninjaInfo.min_weight_male||ninjaInfo.min_weight_female||"-"}–${ninjaInfo.max_weight_male||ninjaInfo.max_weight_female||"-"}lbs`
              )}
            />
            <Detail
              title="Life Expectancy"
              value={pick(
                dogInfo.life_span,
                ninjaInfo.min_life_expectancy
                  ? `${ninjaInfo.min_life_expectancy}–${ninjaInfo.max_life_expectancy} yrs`
                  : null
              )}
            />
            <Detail title="Temperament" value={pick(dogInfo.temperament, ninjaInfo.temperament, "N/A")} />
          </dl>

          <div className="mt-8">
            <h3 className="text-lg font-medium text-gray-700 mb-4">Ratings</h3>
            <div className="space-y-3">
              {[
                { key:"energy", label:"Energy" },
                { key:"shedding", label:"Shedding" },
                { key:"trainability", label:"Trainability" },
                { key:"good_with_children", label:"With Children" },
                { key:"good_with_other_dogs", label:"With Dogs" },
                { key:"good_with_strangers", label:"With Strangers" },
                { key:"playfulness", label:"Playfulness" },
                { key:"protectiveness", label:"Protectiveness" },
                { key:"barking", label:"Barking" },
                { key:"grooming", label:"Grooming" },
                { key:"drooling", label:"Drooling" },
                { key:"coat_length", label:"Coat Length" },
              ].map(({ key, label }) =>
                ninjaInfo[key] != null ? (
                  <MetricBar key={key} label={label} value={ninjaInfo[key]} />
                ) : null
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer button */}
      <div className="px-4 py-4 sm:px-6 bg-gray-50 text-right">
        <button
          onClick={onReset}
          className="inline-flex items-center px-4 py-2 border border-indigo-500 font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Try Another Photo
        </button>
      </div>
    </div>
  );
};

/* ----------------------------------------------------------------------------
   SimilarBreeds – taller, cropped images
---------------------------------------------------------------------------- */
function SimilarBreeds({ labels }) {
  const [breeds, setBreeds] = useState([]);

  useEffect(() => {
    async function fetchSimilar() {
      const candidates = labels.slice(1, 3);
      const results = await Promise.all(
        candidates.map(async (raw) => {
          try {
            const { data } = await axios.get(
              `${import.meta.env.VITE_API}/breed_info`,
              { params: { label: clean(raw) } }
            );
            const { thedogapi, api_ninjas, image_url } = data;
            if (!thedogapi.name && !api_ninjas.name) return null;
            const name = thedogapi.name || api_ninjas.name || clean(raw);
            return {
              id: name,
              name,
              temperament: thedogapi.temperament || api_ninjas.temperament || "",
              image_url,
            };
          } catch {
            return null;
          }
        })
      );
      setBreeds(results.filter(Boolean));
    }
    fetchSimilar();
  }, [labels]);

  if (!breeds.length) return null;

  return (
    <section className="mt-16 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Similar Breeds You Might Be Interested In
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {breeds.map((b) => (
          <div key={b.id} className="bg-white rounded-lg overflow-hidden shadow">
            <div className="w-full aspect-video bg-gray-100 flex items-center justify-center">
              <img
                src={b.image_url}
                alt={b.name}
                className="max-h-full max-w-full object-contain"
              />
            </div>
            <div className="p-4">
              <p className="text-lg font-medium text-gray-900">{b.name}</p>
              {b.temperament && (
                <p className="mt-1 text-sm text-gray-500">{b.temperament}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
