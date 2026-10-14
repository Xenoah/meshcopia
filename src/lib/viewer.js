  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
  import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
  import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
  import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
  import { MTLLoader } from "three/examples/jsm/loaders/MTLLoader.js";
  import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";

  const initialized = new WeakSet();
  const viewerInstances = new WeakMap();
  let occtPromise = null;

  class ArchiveModelViewer {
    constructor(root) {
      this.root = root;
      this.canvas = root.querySelector("canvas");
      this.status = root.querySelector(".model-viewer-status");
      this.src = root.dataset.modelSrc;
      this.type = root.dataset.modelType;
      this.occtBase = root.dataset.occtBase;
      this.isThumbnail = root.dataset.viewerVariant === "thumbnail";
      this.spin = false;
      this.active = true;
      this.disposed = false;
      this.wireframe = false;
      this.materialMode = "original";
      this.lightingMode = "studio";
      this.meshes = [];
      this.resizeFrame = 0;
    }

    async start() {
      this.createScene();
      this.installEvents();
      const object = await this.loadObject();
      if (this.disposed) { object.traverse(i=>{ i.geometry?.dispose(); }); return; }
      this.model = object;
      this.scene.add(object);
      this.collectMeshes(object);
      this.applyMaterial();
      this.applyLighting();
      this.fitCamera(object);
      this.status.textContent = `${this.type.toUpperCase()} preview`;
      this.root.classList.add("is-loaded");

      if (this.isThumbnail) {
        this.draw();
        this.installThumbnailResizeObserver();
        return;
      }

      this.renderer.setAnimationLoop(() => { if (this.active && !document.hidden) this.draw(); });
    }

    createScene() {
      this.scene = new THREE.Scene();
      this.scene.background = null;
      this.camera = new THREE.PerspectiveCamera(42, 1, 0.01, 100000);
      this.camera.position.set(3.2, 2.5, 3.4);

      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true,
        alpha: true,
        preserveDrawingBuffer: this.isThumbnail
      });
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.05;

      this.controls = new OrbitControls(this.camera, this.canvas);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.enabled = !this.isThumbnail;
      this.controls.enableZoom = !this.isThumbnail;
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.controls.enableRotate = !this.isThumbnail;
      this.controls.enablePan = !this.isThumbnail;
      this.controls.autoRotate = this.spin;
      this.controls.autoRotateSpeed = 1.3;

      this.ambientLight = new THREE.AmbientLight(0xffffff, 0.45);
      this.hemiLight = new THREE.HemisphereLight(0xffffff, 0x66706c, 1.0);
      this.keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
      this.fillLight = new THREE.DirectionalLight(0xc7f7f0, 0.55);
      this.scene.add(this.ambientLight, this.hemiLight, this.keyLight, this.fillLight);
    }

    installEvents() {
      this.root.querySelector('[data-action="reset"]')?.addEventListener("click", () => this.fitCamera(this.model));
      this.root.querySelector('[data-action="spin"]')?.addEventListener("click", () => {
        this.spin = !this.spin;
        this.controls.autoRotate = this.spin;
        this.root.querySelector('[data-action="spin"]')?.setAttribute("aria-pressed",String(this.spin));
      });
      this.root.querySelector('[data-action="wire"]')?.addEventListener("click", () => {
        this.wireframe = !this.wireframe;
        this.root.querySelector('[data-action="wire"]')?.setAttribute("aria-pressed",String(this.wireframe));
        this.applyWireframe();
      });
      this.root.querySelector('[data-setting="material"]')?.addEventListener("change", (event) => {
        this.materialMode = event.target.value;
        this.applyMaterial();
      });
      this.root.querySelector('[data-setting="lighting"]')?.addEventListener("change", (event) => {
        this.lightingMode = event.target.value;
        this.applyLighting();
      });
    }

    installThumbnailResizeObserver() {
      if (!("ResizeObserver" in window)) return;
      this.resizeObserver = new ResizeObserver(() => this.requestDraw());
      this.resizeObserver.observe(this.root);
    }

    requestDraw() {
      if (this.resizeFrame) return;
      this.resizeFrame = window.requestAnimationFrame(() => {
        this.resizeFrame = 0;
        this.draw();
      });
    }

    async loadObject() {
      if (this.type === "material") {
        const urls=JSON.parse(this.root.dataset.materialMaps||"{}");
        const loader=new THREE.TextureLoader();
        const mode=this.root.dataset.wrapMode||'repeat';
        const wrapping={repeat:THREE.RepeatWrapping,mirror:THREE.MirroredRepeatWrapping,clamp:THREE.ClampToEdgeWrapping}[mode];
        const textures=Object.fromEntries(await Promise.all(Object.entries(urls).map(async ([key,url])=>{const map=await loader.loadAsync(url);map.wrapS=map.wrapT=wrapping;map.repeat.set(mode==='clamp'?1:2,1);map.colorSpace=key==="baseColor"?THREE.SRGBColorSpace:THREE.NoColorSpace;return [key,map];})));
        return new THREE.Mesh(new THREE.SphereGeometry(1,64,48), new THREE.MeshStandardMaterial({map:textures.baseColor,normalMap:textures.normal,roughnessMap:textures.roughness,roughness:Number(this.root.dataset.roughness??1),metalness:Number(this.root.dataset.metalness)||0}));
      }
      if (["glb","gltf"].includes(this.type)) return (await new GLTFLoader().loadAsync(this.src)).scene;
      if (this.type === "obj") {
        const text = await (await fetch(this.src)).text();
        const loader = new OBJLoader();
        const match = text.match(/^mtllib\s+(.+)$/m);
        if (match) { const materials = await new MTLLoader().loadAsync(new URL(match[1].trim(),new URL(this.src,location.href)).href); materials.preload(); loader.setMaterials(materials); }
        return loader.parse(text);
      }
      if (this.type === "fbx") return this.loadFbx();
      if (this.type === "step") return this.loadStep();
      if (this.type === "stl") return this.loadStl();
      throw new Error(`Unsupported preview type: ${this.type}`);
    }

    loadFbx() {
      this.status.textContent = "Loading FBX";
      const loader = new FBXLoader();
      const resourcePath = this.src.slice(0, this.src.lastIndexOf("/") + 1);
      loader.setResourcePath(resourcePath);
      return new Promise((resolve, reject) => {
        loader.load(this.src, resolve, undefined, reject);
      });
    }

    loadStl() {
      this.status.textContent = "Loading STL";
      const loader = new STLLoader();
      return new Promise((resolve, reject) => {
        loader.load(
          this.src,
          (geometry) => {
            geometry.computeVertexNormals();
            const material = new THREE.MeshStandardMaterial({
              color: 0x5aa89f,
              roughness: 0.5,
              metalness: 0.08
            });
            resolve(new THREE.Mesh(geometry, material));
          },
          undefined,
          reject
        );
      });
    }

    async loadStep() {
      this.status.textContent = "Loading STEP";
      const occt = await loadOcct(this.occtBase);
      const response = await fetch(this.src);
      if (!response.ok) throw new Error(`Failed to fetch STEP: ${response.status}`);
      const buffer = new Uint8Array(await response.arrayBuffer());
      const result = occt.ReadStepFile(buffer, {
        linearUnit: "millimeter",
        linearDeflectionType: "bounding_box_ratio",
        linearDeflection: 0.0008,
        angularDeflection: 0.35
      });
      if (!result.success) throw new Error("STEP import failed");
      const group = new THREE.Group();
      for (const mesh of result.meshes ?? []) group.add(buildStepMesh(mesh));
      return group;
    }

    collectMeshes(object) {
      this.meshes = [];
      object.traverse((item) => {
        if (!item.isMesh) return;
        item.castShadow = true;
        item.receiveShadow = true;
        item.userData.originalMaterial = item.material;
        this.meshes.push(item);
      });
    }

    applyMaterial() {
      for (const mesh of this.meshes) {
        if (mesh.material !== mesh.userData.originalMaterial) {
          for(const m of (Array.isArray(mesh.material)?mesh.material:[mesh.material])) m.dispose();
        }
        if (this.materialMode === "original") {
          mesh.material = mesh.userData.originalMaterial;
        } else {
          mesh.material = this.createMaterial(mesh);
        }
      }
      this.applyWireframe();
    }

    createMaterial(mesh) {
      const baseColor = mesh.userData.viewerColor ?? new THREE.Color(0x5aa89f);
      if (this.materialMode === "metal") {
        return new THREE.MeshStandardMaterial({ color: 0xb7bec2, roughness: 0.28, metalness: 0.72 });
      }
      if (this.materialMode === "plastic") {
        return new THREE.MeshStandardMaterial({ color: baseColor, roughness: 0.38, metalness: 0.0 });
      }
      return new THREE.MeshStandardMaterial({ color: 0xb9c7c1, roughness: 0.74, metalness: 0.04 });
    }

    applyWireframe() {
      for (const mesh of this.meshes) {
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        for (const material of materials) material.wireframe = this.wireframe;
      }
    }

    applyLighting() {
      const modes = {
        studio: { ambient: 0.36, hemi: 1.0, key: 1.32, fill: 0.58, keyPos: [3, 5, 4], fillPos: [-4, 2, -3] },
        soft: { ambient: 0.72, hemi: 0.82, key: 0.62, fill: 0.38, keyPos: [2, 3, 4], fillPos: [-3, 2, 2] },
        front: { ambient: 0.42, hemi: 0.62, key: 1.5, fill: 0.22, keyPos: [0, 1, 5], fillPos: [-2, 1, 2] },
        high: { ambient: 0.24, hemi: 0.64, key: 1.9, fill: 0.38, keyPos: [1, 7, 3], fillPos: [-4, 2, -2] }
      };
      const mode = modes[this.lightingMode] ?? modes.studio;
      this.ambientLight.intensity = mode.ambient;
      this.hemiLight.intensity = mode.hemi;
      this.keyLight.intensity = mode.key;
      this.fillLight.intensity = mode.fill;
      this.keyLight.position.set(...mode.keyPos);
      this.fillLight.position.set(...mode.fillPos);
    }

    fitCamera(object) {
      if (!object) return;
      const box = new THREE.Box3().setFromObject(object);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      object.position.sub(center);
      const radius = Math.max(size.length() / 2, .001);
      const aspect = Math.max(this.root.clientWidth / Math.max(this.root.clientHeight,1),.2);
      const fov = THREE.MathUtils.degToRad(42);
      const distance = radius / Math.sin(Math.min(fov,2*Math.atan(Math.tan(fov/2)*aspect))/2) * .82;
      this.camera.near = Math.max(distance / 1000, 0.01);
      this.camera.far = distance * 1000;
      this.camera.position.set(distance * 0.9, distance * 0.68, distance * 0.92);
      this.camera.updateProjectionMatrix();
      this.controls.target.set(0, 0, 0);
      this.controls.update();
    }

    draw() {
      const rect = this.root.getBoundingClientRect();
      if (!rect.width || !rect.height || this.disposed) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.floor(rect.width * dpr));
      const height = Math.max(1, Math.floor(rect.height * dpr));
      if (this.canvas.width !== width || this.canvas.height !== height) {
        this.renderer.setSize(rect.width, rect.height, false);
        this.camera.aspect = rect.width / rect.height;
        this.camera.updateProjectionMatrix();
      }
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    }
  }

  function buildStepMesh(resultMesh) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(flattenArray(resultMesh.attributes.position.array), 3));
    if (resultMesh.attributes.normal) {
      geometry.setAttribute("normal", new THREE.Float32BufferAttribute(flattenArray(resultMesh.attributes.normal.array), 3));
    } else {
      geometry.computeVertexNormals();
    }
    geometry.setIndex(new THREE.BufferAttribute(Uint32Array.from(flattenArray(resultMesh.index.array)), 1));
    const color = resultMesh.color ? new THREE.Color(resultMesh.color[0], resultMesh.color[1], resultMesh.color[2]) : new THREE.Color(0x9fb8b2);
    const material = new THREE.MeshStandardMaterial({ color, roughness: 0.48, metalness: 0.05 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = resultMesh.name || "STEP mesh";
    mesh.userData.viewerColor = color;
    return mesh;
  }

  function flattenArray(value) {
    return Array.isArray(value?.[0]) ? value.flat() : value;
  }

  async function loadOcct(base) {
    if (!occtPromise) {
      occtPromise = loadScript(`${base}/occt-import-js.js`).then(() =>
        window.occtimportjs({
          locateFile: (fileName) => `${base}/${fileName}`
        })
      );
    }
    return occtPromise;
  }

  function loadScript(src) {
    if (document.querySelector(`script[src="${src}"]`)) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.append(script);
    });
  }

  function initModelViewers() {
    document.querySelectorAll('.model-viewer-3d[data-viewer-autoload="true"]').forEach(startModelViewer);
  }

  export function startModelViewer(root) {
    if (!root) return;
    const prior = viewerInstances.get(root);
    if (prior && prior.src === root.dataset.modelSrc && !prior.disposed) { prior.active=true; return; }
    if (prior) {
      prior.disposed=true; prior.renderer?.setAnimationLoop(null); prior.controls?.dispose(); prior.renderer?.dispose();
      prior.model?.traverse(item => { item.geometry?.dispose(); for(const m of new Set([...(Array.isArray(item.material)?item.material:[item.material]), ...(Array.isArray(item.userData.originalMaterial)?item.userData.originalMaterial:[item.userData.originalMaterial])])) { if(!m) continue; for(const v of Object.values(m)) if(v?.isTexture) v.dispose(); m.dispose(); } });
      initialized.delete(root);
    }
    root.classList.remove("is-loaded"); root.dataset.loaded="false";
    root.querySelectorAll('[aria-pressed]').forEach(button=>button.setAttribute('aria-pressed','false'));
    const materialSelect=root.querySelector('[data-setting="material"]');
    const lightingSelect=root.querySelector('[data-setting="lighting"]');
    if(materialSelect) materialSelect.value='original';
    if(lightingSelect) lightingSelect.value='studio';
    initialized.add(root);
    const viewer = new ArchiveModelViewer(root);
    viewerInstances.set(root, viewer);
    viewer.start().then(() => {
      if(viewer.disposed) return;
      root.dataset.loaded = "true";
    }).catch((error) => {
      if(viewer.disposed) return;
      viewer.disposed=true; viewer.renderer?.setAnimationLoop(null); viewer.renderer?.dispose(); viewer.controls?.dispose();
      root.dataset.loaded = "error";
      initialized.delete(root);
      root.querySelector(".model-viewer-status").textContent = "3Dプレビューを読み込めません。ファイルはダウンロードできます。";
      console.error(error);
    });
  }


  window.addEventListener('meshcopia-viewer-pause', event => { const viewer=viewerInstances.get(event.detail?.root); if(viewer) viewer.active=false; });
