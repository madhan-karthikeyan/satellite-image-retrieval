import { createFileRoute } from "@tanstack/react-router";
import { useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import {
  Upload,
  MousePointer2,
  Play,
  Image,
  FolderOpen,
  Save,
  Loader2,
  Plus,
  Trash2,
  Layers,
  Target,
} from "lucide-react";
import { api, type SearchResult, type ChipUploadResponse } from "@/utils/api";

export const Route = createFileRoute("/")({
  component: HomeComponent,
});

type InputMode = "upload" | "draw";
type Tab = "input" | "results";

const OBJECT_CLASSES = [
  "Playground",
  "Brick Kiln",
  "Metro Shed",
  "Pond-1 (Dried)",
  "Pond-2 (Filled)",
  "Sheds",
  "Solar Panel",
  "STP",
  "Custom",
];

function HomeComponent() {
  const [inputMode, setInputMode] = useState<InputMode>("upload");
  const [activeTab, setActiveTab] = useState<Tab>("input");
  const [objectName, setObjectName] = useState("");
  const [customObjectName, setCustomObjectName] = useState("");
  const [targetDirectory, setTargetDirectory] = useState("");
  const [outputDirectory, setOutputDirectory] = useState("");
  const [similarityThreshold, setSimilarityThreshold] = useState(0.65);
  const [uploadedChips, setUploadedChips] = useState<ChipUploadResponse[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [drawnBoxes, setDrawnBoxes] = useState<Array<{ x: number; y: number; w: number; h: number }>>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleFileUpload = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      if (!objectName && !customObjectName) {
        toast.error("Please select or enter an object name");
        return;
      }

      const name = objectName === "Custom" ? customObjectName : objectName;
      setIsUploading(true);

      try {
        for (const file of Array.from(files)) {
          const response = await api.uploadChip(file, name);
          setUploadedChips((prev) => [...prev, response]);
          toast.success(`Uploaded: ${file.name}`);
        }
      } catch (error) {
        toast.error(`Upload failed: ${error}`);
      } finally {
        setIsUploading(false);
      }
    },
    [objectName, customObjectName]
  );

  const handleSearch = useCallback(async () => {
    if (!targetDirectory) {
      toast.error("Please select target directory");
      return;
    }
    if (!outputDirectory) {
      toast.error("Please select output directory");
      return;
    }
    if (uploadedChips.length === 0) {
      toast.error("Please upload at least one image chip");
      return;
    }

    setIsSearching(true);
    setActiveTab("results");

    try {
      const searchObjectName =
        objectName === "Custom" ? customObjectName : objectName;

      const response = await api.executeSearch({
        object_name: searchObjectName,
        target_directory: targetDirectory,
        output_directory: outputDirectory,
        similarity_threshold: similarityThreshold,
        batch_name: "TeamSatVision",
      });

      if (response.success) {
        setSearchResults(response.results);
        toast.success(`Found ${response.results_count} matches`);
      } else {
        toast.error(response.message);
      }
    } catch (error) {
      toast.error(`Search failed: ${error}`);
    } finally {
      setIsSearching(false);
    }
  }, [
    targetDirectory,
    outputDirectory,
    uploadedChips,
    objectName,
    customObjectName,
    similarityThreshold,
  ]);

  const handleImageSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const dir = e.target.value;
      if (!dir) return;

      try {
        const response = await api.listImagery(dir);
        if (response.imagery_count > 0) {
          const firstImage = response.imagery_list[0].filename;
          setSelectedImage(
            await api.getImageryPreview(firstImage, dir)
          );
          setTargetDirectory(dir);
          toast.success(`Loaded ${response.imagery_count} images`);
        } else {
          toast.warning("No images found in directory");
        }
      } catch {
        toast.error("Failed to load images");
      }
    },
    []
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLImageElement>) => {
      if (inputMode !== "draw" || !imageRef.current) return;

      const rect = imageRef.current.getBoundingClientRect();
      const scaleX = imageRef.current.naturalWidth / rect.width;
      const scaleY = imageRef.current.naturalHeight / rect.height;

      setIsDrawing(true);
      setDrawStart({
        x: Math.round((e.clientX - rect.left) * scaleX),
        y: Math.round((e.clientY - rect.top) * scaleY),
      });
    },
    [inputMode]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLImageElement>) => {
      if (!isDrawing || !drawStart || !imageRef.current) return;

      const rect = imageRef.current.getBoundingClientRect();
      const scaleX = imageRef.current.naturalWidth / rect.width;
      const scaleY = imageRef.current.naturalHeight / rect.height;

      const currentX = Math.round((e.clientX - rect.left) * scaleX);
      const currentY = Math.round((e.clientY - rect.top) * scaleY);

      const box = {
        x: Math.min(drawStart.x, currentX),
        y: Math.min(drawStart.y, currentY),
        w: Math.abs(currentX - drawStart.x),
        h: Math.abs(currentY - drawStart.y),
      };

      setDrawnBoxes([box]);
    },
    [isDrawing, drawStart]
  );

  const handleMouseUp = useCallback(async () => {
    if (!isDrawing || drawnBoxes.length === 0) return;

    setIsDrawing(false);

    if (drawnBoxes[0].w < 10 || drawnBoxes[0].h < 10) {
      toast.warning("Box too small. Please draw a larger area.");
      return;
    }

    const box = drawnBoxes[0];
    const name = objectName === "Custom" ? customObjectName : objectName;

    if (!name) {
      toast.error("Please select or enter an object name first");
      setDrawnBoxes([]);
      return;
    }

    toast.info("Cropping selected area...");
  }, [isDrawing, drawnBoxes, objectName, customObjectName]);

  const handleConfirmBox = useCallback(async () => {
    if (drawnBoxes.length === 0 || !selectedImage) return;

    const box = drawnBoxes[0];
    const name = objectName === "Custom" ? customObjectName : objectName;

    try {
      const response = await api.uploadChipFromBox(
        new File([], "drawn_chip.tif"),
        name,
        {
          x_min: box.x,
          y_min: box.y,
          x_max: box.x + box.w,
          y_max: box.y + box.h,
        }
      );

      setUploadedChips((prev) => [...prev, response as ChipUploadResponse]);
      toast.success("Chip extracted from drawn box");
      setDrawnBoxes([]);
    } catch (error) {
      toast.error(`Failed to extract chip: ${error}`);
    }
  }, [drawnBoxes, selectedImage, objectName, customObjectName]);

  const removeChip = useCallback((index: number) => {
    setUploadedChips((prev) => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Visual Search
          </h1>
          <p className="text-muted-foreground mt-1">
            Search and detect objects in satellite imagery
          </p>
        </div>
      </div>

      <div className="flex gap-2 p-1 bg-secondary/30 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab("input")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "input"
              ? "bg-primary text-primary-foreground shadow-lg"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Input Configuration
        </button>
        <button
          onClick={() => setActiveTab("results")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            activeTab === "results"
              ? "bg-primary text-primary-foreground shadow-lg"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Results
          {searchResults.length > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-accent text-accent-foreground text-xs">
              {searchResults.length}
            </span>
          )}
        </button>
      </div>

      {activeTab === "input" ? (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border bg-card p-6 space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Layers className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Input Mode</h2>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <button
                  onClick={() => setInputMode("upload")}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    inputMode === "upload"
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="w-8 h-8" />
                    <span className="font-medium">Upload Chips</span>
                    <span className="text-xs text-muted-foreground">
                      Upload image samples
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => setInputMode("draw")}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    inputMode === "draw"
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="flex flex-col items-center gap-2">
                    <MousePointer2 className="w-8 h-8" />
                    <span className="font-medium">Draw Box</span>
                    <span className="text-xs text-muted-foreground">
                      Select area on imagery
                    </span>
                  </div>
                </button>
              </div>
            </div>

            <div className="rounded-2xl border bg-card p-6 space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Object Selection</h2>
              </div>

              <div className="grid grid-cols-3 gap-2">
                {OBJECT_CLASSES.map((cls) => (
                  <button
                    key={cls}
                    onClick={() => setObjectName(cls)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      objectName === cls
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary/50 hover:bg-secondary"
                    }`}
                  >
                    {cls}
                  </button>
                ))}
              </div>

              {objectName === "Custom" && (
                <input
                  type="text"
                  placeholder="Enter custom object name..."
                  value={customObjectName}
                  onChange={(e) => setCustomObjectName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg bg-secondary/50 border border-border focus:border-primary focus:outline-none transition-colors"
                />
              )}
            </div>

            <div className="rounded-2xl border bg-card p-6 space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <FolderOpen className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Directories</h2>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">
                    Target Imagery Directory
                  </label>
                  <input
                    type="text"
                    placeholder="/path/to/satellite/images"
                    value={targetDirectory}
                    onChange={(e) => setTargetDirectory(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg bg-secondary/50 border border-border focus:border-primary focus:outline-none transition-colors font-mono text-sm"
                  />
                  {inputMode === "draw" && (
  <>
    <input
      type="file"
      webkitdirectory="true"
      onChange={handleImageSelect}
      className="hidden"
      id="folder-select"
    />
    <label
      htmlFor="folder-select"
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary/50 border border-border hover:border-primary cursor-pointer transition-colors text-sm"
    >
      <FolderOpen className="w-4 h-4" />
      Browse Folder
    </label>
  </>
)}
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">
                    Output Directory
                  </label>
                  <input
                    type="text"
                    placeholder="/path/to/output"
                    value={outputDirectory}
                    onChange={(e) => setOutputDirectory(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg bg-secondary/50 border border-border focus:border-primary focus:outline-none transition-colors font-mono text-sm"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">
                  Similarity Threshold: {similarityThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border bg-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Image className="w-5 h-5 text-primary" />
                  <h2 className="text-lg font-semibold">Image Chips</h2>
                </div>
                <span className="text-xs text-muted-foreground">
                  {uploadedChips.length}/5
                </span>
              </div>

              {inputMode === "upload" && (
                <div>
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                    id="chip-upload"
                    disabled={uploadedChips.length >= 5}
                  />
                  <label
                    htmlFor="chip-upload"
                    className={`flex items-center justify-center gap-2 w-full p-4 rounded-xl border-2 border-dashed cursor-pointer transition-all ${
                      uploadedChips.length >= 5
                        ? "border-muted-foreground/30 cursor-not-allowed opacity-50"
                        : "border-primary/50 hover:border-primary hover:bg-primary/5"
                    }`}
                  >
                    {isUploading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Plus className="w-5 h-5" />
                    )}
                    <span>Upload Chips</span>
                  </label>
                </div>
              )}

              {inputMode === "draw" && selectedImage && (
                <div
                  ref={containerRef}
                  className="relative rounded-xl overflow-hidden border border-border"
                >
                  <img
                    ref={imageRef}
                    src={selectedImage}
                    alt="Satellite imagery"
                    className="w-full cursor-crosshair"
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                  />
                  {drawnBoxes.map((box, i) => (
                    <div
                      key={i}
                      className="absolute border-2 border-primary bg-primary/20 pointer-events-none"
                      style={{
                        left: box.x / (imageRef.current?.naturalWidth || 1) * 100 + "%",
                        top: box.y / (imageRef.current?.naturalHeight || 1) * 100 + "%",
                        width: box.w / (imageRef.current?.naturalWidth || 1) * 100 + "%",
                        height: box.h / (imageRef.current?.naturalHeight || 1) * 100 + "%",
                      }}
                    />
                  ))}
                  <button
                    onClick={handleConfirmBox}
                    disabled={drawnBoxes.length === 0}
                    className="absolute bottom-2 right-2 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50"
                  >
                    Confirm Selection
                  </button>
                </div>
              )}

              <div className="space-y-2">
                {uploadedChips.map((chip, i) => (
                  <div
                    key={chip.chip_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
                  >
                    <div>
                      <p className="text-sm font-medium">{chip.chip_info.object_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {chip.chip_info.width}x{chip.chip_info.height}
                      </p>
                    </div>
                    <button
                      onClick={() => removeChip(i)}
                      className="p-1.5 rounded-lg hover:bg-destructive/20 text-destructive transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleSearch}
              disabled={isSearching || uploadedChips.length === 0}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-primary to-accent text-primary-foreground font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Start Visual Search
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {searchResults.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Target className="w-16 h-16 mb-4 opacity-30" />
              <p>No search results yet</p>
              <p className="text-sm">Run a search to see results here</p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <p className="text-muted-foreground">
                  Found {searchResults.length} matches
                </p>
                <button
                  onClick={() => {
                    const blob = new Blob(
                      [
                        searchResults
                          .map(
                            (r) =>
                              `${r.x_min} ${r.y_min} ${r.x_max} ${r.y_max} ${r.searched_object_name} ${r.target_imagery_file_name} ${r.similarity_score}`
                          )
                          .join("\n"),
                      ],
                      { type: "text/plain" }
                    );
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "GC_PS03_results.txt";
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors text-sm"
                >
                  <Save className="w-4 h-4" />
                  Export Results
                </button>
              </div>

              <div className="grid gap-4">
                {searchResults.map((result, i) => (
                  <div
                    key={i}
                    className="rounded-xl border bg-card p-4 flex items-center gap-4"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 rounded-lg bg-primary/20 text-primary text-xs font-medium">
                          {result.searched_object_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {result.target_imagery_file_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>
                          BBox: ({result.x_min}, {result.y_min}) - ({result.x_max}, {result.y_max})
                        </span>
                        <span className="text-primary font-medium">
                          {result.similarity_score.toFixed(3)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
