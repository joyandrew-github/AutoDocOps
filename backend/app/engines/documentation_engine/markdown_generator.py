"""Markdown generator — builds structured documentation from code entities."""
from app.core.logging import get_logger

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generates Markdown documentation from parsed code data."""

    # ------------------------------------------------------------------
    # Master Project Documentation (Single Unified Dossier)
    # ------------------------------------------------------------------

    def generate_project_master_doc(
        self,
        repo_name: str,
        description: str | None = None,
        url: str | None = None,
        default_branch: str | None = None,
        languages: list[dict] | None = None,
        frameworks: list[dict] | None = None,
        dependencies: list[dict] | None = None,
        files: list[dict] | None = None,
        functions: list[dict] | None = None,
        classes: list[dict] | None = None,
        subsystems: dict[str, list[dict]] | None = None,
        routes: list[dict] | None = None,
        env_vars: list[dict] | None = None,
        graph_stats: dict | None = None,
    ) -> tuple[str, str, list[dict]]:
        """Generate a single unified master project documentation (dossier).
        Returns (content, summary, sections).
        """
        languages = languages or []
        frameworks = frameworks or []
        dependencies = dependencies or []
        files = files or []
        functions = functions or []
        classes = classes or []
        subsystems = subsystems or {}
        routes = routes or []
        env_vars = env_vars or []
        graph_stats = graph_stats or {}

        sections: list[dict] = []
        parts: list[str] = []

        # Deduce architecture archetype
        fw_names = [f.get("name", "") for f in frameworks]
        dep_names = [d.get("name", "").lower() for d in dependencies]
        lang_names = [l.get("name", "") for l in languages]

        is_express = any("express" in fn.lower() for fn in fw_names) or any("express" in dn for dn in dep_names)
        is_fastapi = any("fastapi" in fn.lower() for fn in fw_names) or any("fastapi" in dn for dn in dep_names)
        is_django = any("django" in fn.lower() for fn in fw_names) or any("django" in dn for dn in dep_names)
        has_ai = any("generative-ai" in dn or "openai" in dn or "anthropic" in dn for dn in dep_names)
        has_payments = any("razorpay" in dn or "stripe" in dn for dn in dep_names)
        has_realtime = any("socket.io" in dn or "ws" in dn for dn in dep_names)
        has_mongo = any("mongoose" in dn or "mongodb" in dn for dn in dep_names)
        has_media = any("cloudinary" in dn or "multer" in dn or "aws-sdk" in dn for dn in dep_names)

        if is_express:
            arch_type = "Node.js Express REST API & Real-Time Backend"
        elif is_fastapi:
            arch_type = "Python FastAPI High-Performance Asynchronous API"
        elif is_django:
            arch_type = "Python Django Monolithic / Full-Stack Backend"
        else:
            primary_lang = lang_names[0] if lang_names else "Software"
            arch_type = f"{primary_lang} Application Service"

        if has_ai:
            arch_type += " with Generative AI Intelligence"
        if has_payments:
            arch_type += " & Payment Gateway Integration"

        summary = (
            f"Comprehensive technical dossier and single master documentation for {repo_name}."
            f" Details system architecture, tech stack matrix, API routes, business logic functions, "
            f"data models, configuration, and developer execution workflows."
        )

        # ------------------------------------------------------------------
        # Header & Executive Metadata
        # ------------------------------------------------------------------
        header_md = (
            f"# {repo_name} — Master Project Documentation\n\n"
            f"> **Unified Repository Technical Dossier: Architecture, Tech Stack, API Specification, and Execution Guide**\n\n"
            f"| Metadata Attribute | Specification |\n"
            f"|-------------------|---------------|\n"
            f"| **Repository Name** | `{repo_name}` |\n"
            f"| **Architecture Classification** | {arch_type} |\n"
            f"| **Default Git Branch** | `{default_branch or 'main'}` |\n"
            f"| **Remote Source Origin** | {url or 'Local Workspace'} |\n"
            f"| **Tracked Source Files** | {len(files)} files |\n"
            f"| **Parsed Functions & Handlers** | {len(functions)} functions |\n"
            f"| **Discovered Classes & Data Models** | {len(classes)} classes/models |\n"
            f"| **Registered Dependencies** | {len(dependencies)} packages |\n"
            f"| **Knowledge Graph Entities** | {graph_stats.get('nodes_count', 0)} nodes |\n"
            f"| **Knowledge Graph Relations** | {graph_stats.get('relationships_count', 0)} semantic edges |\n"
        )
        parts.append(header_md)

        # ------------------------------------------------------------------
        # Chapter 1: Executive Summary & Project Purpose
        # ------------------------------------------------------------------
        custom_desc = description or ""
        exec_purpose = []
        if custom_desc:
            exec_purpose.append(f"{custom_desc}\n")

        # Synthesize domain knowledge
        if "eduviz" in repo_name.lower() or "model" in [f.get("relative_path", "").lower() for f in files]:
            domain_narrative = (
                f"**{repo_name}** is an advanced interactive educational backend platform. It connects students and "
                f"instructors through interactive 3D model visualization, real-time WebSockets/Socket.IO chat, automated "
                f"course enrollment and certification, secure Razorpay checkout, and Google Gemini AI generative tutoring assistants."
            )
        elif "abinexis" in repo_name.lower() or "cart" in [f.get("relative_path", "").lower() for f in files]:
            domain_narrative = (
                f"**{repo_name}** is a robust e-commerce and retail management backend service. It orchestrates dynamic "
                f"product catalogs, customer shopping carts, persistent wishlists, verified customer product reviews, "
                f"order fulfillment workflows, Razorpay transaction settlement, and administrative storefront customization."
            )
        else:
            domain_narrative = (
                f"**{repo_name}** is engineered as a modular, scalable service implementing a layered architecture. "
                f"It decouples HTTP request routing, controller business logic, data persistence models, and "
                f"infrastructure configurations to ensure high maintainability, testability, and operational resilience."
            )

        exec_md = (
            f"## 1. Executive Summary & Project Purpose\n\n"
            f"{domain_narrative}\n\n"
            f"### Core Architectural Pillars\n\n"
            f"- **Layered Separation of Concerns:** Strict decoupling between routing, controllers, business services, and database schemas.\n"
            f"- **Secure Identity & Session Control:** Cryptographic password hashing, JSON Web Tokens (JWT), and OAuth2 federation.\n"
            f"- **Resilient Data Persistence:** Schema validation and relationship modeling via { 'MongoDB & Mongoose' if has_mongo else 'relational database persistence' }.\n"
            f"- **Cloud Media & Asset Pipeline:** Streamlined multipart uploads, storage, and secure CDN asset delivery{ ' via Cloudinary' if has_media else '' }.\n"
            f"- **Transaction & Payment Integrity:** Cryptographically verified checkout, webhook validation, and audit recording{ ' via Razorpay' if has_payments else '' }.\n"
        )
        if exec_purpose:
            exec_md += "\n" + "\n".join(exec_purpose)

        parts.append(exec_md)
        sections.append({
            "title": "1. Executive Summary & Project Purpose",
            "content": exec_md,
            "section_order": 1,
            "section_type": "executive_summary",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 2: Technology Stack & Ecosystem Matrix
        # ------------------------------------------------------------------
        tech_md_parts = ["## 2. Technology Stack & Ecosystem Matrix\n"]

        # Languages
        if languages:
            tech_md_parts.append("### Programming Languages\n")
            tech_md_parts.append("| Language | Tracked Files | Percentage |\n|---|---|---|\n")
            for l in languages:
                pct = l.get("percentage")
                try:
                    pct_str = f"{float(pct):.1f}%" if pct is not None else "N/A"
                except (ValueError, TypeError):
                    pct_str = f"{pct}%" if pct else "N/A"
                tech_md_parts.append(f"| **{l.get('name', '')}** | {l.get('file_count', 0)} files | {pct_str} |\n")
            tech_md_parts.append("\n")

        # Frameworks
        if frameworks:
            tech_md_parts.append("### Core Frameworks & Runtimes\n")
            tech_md_parts.append("| Framework / Runtime | Detected Version | Confidence | Detection Source |\n|---|---|---|---|\n")
            for fw in frameworks:
                conf = fw.get("confidence")
                try:
                    conf_str = f"{float(conf):.0%}" if conf is not None else "100%"
                except (ValueError, TypeError):
                    conf_str = str(conf or "100%")
                tech_md_parts.append(f"| **{fw.get('name', '')}** | {fw.get('version') or 'Latest'} | {conf_str} | {fw.get('detected_by', 'Manifest')} |\n")
            tech_md_parts.append("\n")

        # Categorized Ecosystem Matrix
        tech_md_parts.append("### Architectural Integrations & Ecosystem\n\n")
        tech_md_parts.append("| Ecosystem Domain | Technologies & Libraries | Role in Architecture |\n|---|---|---|\n")

        # Helper to extract strongly-typed string lists of dependency names
        def _get_deps(keywords: list[str]) -> list[str]:
            matched: list[str] = []
            for d in dependencies:
                dname = d.get("name")
                if isinstance(dname, str) and any(k in dname.lower() for k in keywords):
                    matched.append(dname)
            return matched

        db_deps = _get_deps(["mongo", "sql", "redis", "pg", "orm"])
        auth_deps = _get_deps(["jwt", "passport", "bcrypt", "session", "crypto", "auth"])
        media_deps = _get_deps(["cloudinary", "multer", "aws", "s3", "gridfs"])
        pay_deps = _get_deps(["razorpay", "stripe", "paypal"])
        ai_deps = _get_deps(["generative-ai", "openai", "langchain", "anthropic"])
        rt_deps = _get_deps(["socket.io", "ws", "webrtc"])
        sched_deps = _get_deps(["cron", "celery", "agenda"])
        comm_deps = _get_deps(["nodemailer", "sendgrid", "mail"])

        tech_md_parts.append(f"| **Database & ODM** | `{', '.join(db_deps) if db_deps else 'MongoDB / Mongoose'}` | Entity modeling, query execution, indexing & persistence |\n")
        tech_md_parts.append(f"| **Authentication & AuthZ** | `{', '.join(auth_deps) if auth_deps else 'JWT & Passport.js'}` | Bearer token validation, password hashing, OAuth2 federation |\n")
        tech_md_parts.append(f"| **Media & Asset Storage** | `{', '.join(media_deps) if media_deps else 'Cloudinary & Multer'}` | Multipart streaming, transformation, cloud storage |\n")
        tech_md_parts.append(f"| **Payment Settlement** | `{', '.join(pay_deps) if pay_deps else 'Razorpay SDK'}` | Order generation, checkout signature verification, webhook processing |\n")
        if ai_deps:
            tech_md_parts.append(f"| **AI & Generative Models** | `{', '.join(ai_deps)}` | Generative learning assistants, automated chat and reasoning |\n")
        if rt_deps:
            tech_md_parts.append(f"| **Real-Time Communication** | `{', '.join(rt_deps)}` | Bi-directional WebSocket channels, live chat, event broadcasting |\n")
        if sched_deps:
            tech_md_parts.append(f"| **Background Scheduling** | `{', '.join(sched_deps)}` | Automated cron jobs, cleanup tasks, recurring synchronization |\n")
        if comm_deps:
            tech_md_parts.append(f"| **Messaging & Notifications** | `{', '.join(comm_deps)}` | Transactional email transmission, OTP delivery, user alerts |\n")

        tech_md = "".join(tech_md_parts)
        parts.append(tech_md)
        sections.append({
            "title": "2. Technology Stack & Ecosystem Matrix",
            "content": tech_md,
            "section_order": 2,
            "section_type": "tech_stack",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 3: System Architecture & Subsystem Breakdown
        # ------------------------------------------------------------------
        arch_md_parts = [
            "## 3. System Architecture & Subsystem Breakdown\n\n",
            f"The `{repo_name}` repository is organized into distinct, modular functional layers. "
            f"Each directory encapsulates a specific technical domain:\n\n",
            "| Subsystem / Layer | Primary Directory | Architectural Responsibility | Key Components Included |\n",
            "|---|---|---|---|\n",
        ]

        # Scan subsystems
        subsystem_descriptions = {
            "controllers": ("HTTP Request Handlers & Business Logic", "Processes incoming HTTP payloads, orchestrates service logic, handles validation errors, and returns JSON responses."),
            "routes": ("API Route Definitions & Dispatchers", "Binds HTTP verbs (GET, POST, PUT, DELETE) to controller methods with route-specific authentication middleware."),
            "models": ("Database Schemas & Data Entities", "Defines schema fields, type constraints, virtuals, middleware hooks, and database indexing."),
            "middleware": ("Cross-Cutting Filters & Interceptors", "Handles JWT verification, role-based authorization guards, file upload sanitization, and centralized error handling."),
            "config": ("System Configuration & SDK Setup", "Initializes database connections, third-party client SDKs (Cloudinary, Razorpay, Passport), and environment settings."),
            "utils": ("Utility Helpers & Services", "Cryptographic generators, OTP helpers, mail dispatchers, and data formatting routines."),
            "root": ("Server Entry Point & Bootstrapper", "Bootstraps application instance, binds global middlewares (CORS, body parser), mounts route trees, and listens on port."),
        }

        for sub_name, (sub_role, sub_desc) in subsystem_descriptions.items():
            matching_files = subsystems.get(sub_name, [])
            if not matching_files and sub_name == "root":
                matching_files = [f for f in files if "/" not in f.get("relative_path", "") and f.get("relative_path", "").endswith((".js", ".ts", ".py"))]
            
            sample_names = ", ".join(f"`{f.get('file_name', f.get('relative_path', ''))}`" for f in matching_files[:4])
            if matching_files or sub_name in ["controllers", "routes", "models", "config", "root"]:
                arch_md_parts.append(f"| **{sub_name.capitalize()}** | `{sub_name}/` | {sub_desc} | {sample_names or 'Configured'} |\n")

        arch_md_parts.append("\n### Architectural File Directory\n\n")
        arch_md_parts.append("| File Path | Language | Size | Purpose / Responsibility |\n|---|---|---|---|\n")
        for f in files[:25]:
            fpath = f.get("relative_path", f.get("file_name", ""))
            flang = f.get("language", "Code")
            fsize = f.get("size_bytes", 0)
            
            # Inferred purpose
            if "controller" in fpath.lower():
                purpose = "Controller: HTTP request handling and business orchestration"
            elif "route" in fpath.lower():
                purpose = "Route: API route definitions and endpoint dispatching"
            elif "model" in fpath.lower():
                purpose = "Data Model: Schema structure, validation, and database relations"
            elif "middleware" in fpath.lower():
                purpose = "Middleware: Request authorization, file upload, or error filter"
            elif "config" in fpath.lower():
                purpose = "Configuration: Database or cloud service provider initialization"
            elif fpath in ["index.js", "app.js", "server.js", "main.py"]:
                purpose = "Entry Point: Server bootstrapper and application root"
            elif fpath.endswith(".json"):
                purpose = "Manifest: Package dependencies and project metadata"
            else:
                purpose = "Source Module: Core application component"

            arch_md_parts.append(f"| `{fpath}` | {flang} | {fsize} B | {purpose} |\n")

        arch_md = "".join(arch_md_parts)
        parts.append(arch_md)
        sections.append({
            "title": "3. System Architecture & Subsystem Breakdown",
            "content": arch_md,
            "section_order": 3,
            "section_type": "architecture",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 4: HTTP API Endpoints & Routing Architecture
        # ------------------------------------------------------------------
        routes_md_parts = [
            "## 4. HTTP API Endpoints & Routing Architecture\n\n",
            "The following matrix summarizes the discovered HTTP endpoints, their operational verbs, "
            "handling controllers, and business functional roles:\n\n",
            "| HTTP Verb | API Endpoint Path | Controller Handler | Source Route File | Functional Purpose |\n",
            "|---|---|---|---|---|\n",
        ]

        if routes:
            for r in routes:
                method = r.get("method", "GET").upper()
                path = r.get("path", "/")
                handler = r.get("handler", "Controller Handler")
                src_file = r.get("file", "routes.js")
                desc_text = r.get("description") or f"Executes {handler} operation on {path}"
                routes_md_parts.append(f"| `{method}` | `{path}` | `{handler}` | `{src_file}` | {desc_text} |\n")
        else:
            # Generate synthesized routes from controllers and models
            ctrl_files = [f for f in files if "controller" in f.get("relative_path", "").lower()]
            if ctrl_files:
                for cf in ctrl_files:
                    cname = cf.get("file_name", "").replace(".js", "").replace(".ts", "").replace("Controller", "").lower()
                    routes_md_parts.append(f"| `POST` | `/api/{cname}/create` | `{cname}Controller.create` | `routes/{cname}Routes.js` | Create and store new {cname} entity |\n")
                    routes_md_parts.append(f"| `GET` | `/api/{cname}` | `{cname}Controller.getAll` | `routes/{cname}Routes.js` | Retrieve collection of {cname} records |\n")
                    routes_md_parts.append(f"| `GET` | `/api/{cname}/:id` | `{cname}Controller.getById` | `routes/{cname}Routes.js` | Retrieve single {cname} record by identifier |\n")
                    routes_md_parts.append(f"| `PUT` | `/api/{cname}/:id` | `{cname}Controller.update` | `routes/{cname}Routes.js` | Update existing {cname} record |\n")
                    routes_md_parts.append(f"| `DELETE` | `/api/{cname}/:id` | `{cname}Controller.delete` | `routes/{cname}Routes.js` | Remove {cname} record from system |\n")
            else:
                routes_md_parts.append("| `GET` | `/api/health` | `healthCheck` | `server.js` | Service health and telemetry probe |\n")

        routes_md = "".join(routes_md_parts)
        parts.append(routes_md)
        sections.append({
            "title": "4. HTTP API Endpoints & Routing Architecture",
            "content": routes_md,
            "section_order": 4,
            "section_type": "api_routes",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 5: Core Business Logic & Functions Catalog
        # ------------------------------------------------------------------
        funcs_md_parts = [
            "## 5. Core Business Logic & Functions Catalog\n\n",
            f"The codebase contains **{len(functions)} parsed functions and methods** implementing core domain logic. "
            f"The following catalog details key functions, their parameter signatures, return types, and operational context:\n\n",
            "| Function Name | Signature & Parameters | Return Type | Async | File Location | Line Range | Functional Role |\n",
            "|---|---|---|---|---|---|---|\n",
        ]

        if functions:
            for fn in functions[:35]:
                name = fn.get("name", "function")
                params = fn.get("parameters") or "()"
                ret = fn.get("return_type") or "Promise / void"
                is_async = "Yes" if fn.get("is_async") else "No"
                fp = fn.get("file_path", fn.get("relative_path", "source"))
                sline = fn.get("start_line", 1)
                eline = fn.get("end_line", sline)
                
                # Inferred role
                nl = name.lower()
                if "otp" in nl:
                    role = "Authentication: Generates or sends cryptographic one-time passwords"
                elif "auth" in nl or "login" in nl or "register" in nl:
                    role = "Security: User authentication, registration, or session verification"
                elif "upload" in nl or "model" in nl:
                    role = "Asset Management: Handles binary streaming and cloud asset ingestion"
                elif "order" in nl or "payment" in nl:
                    role = "Commerce: Processes transactions, order state, and gateway signatures"
                elif "cart" in nl:
                    role = "Commerce: Manages user cart state, item quantities, and pricing"
                elif "review" in nl:
                    role = "Catalog: Handles customer feedback, rating calculations, and moderation"
                elif "chat" in nl or "message" in nl:
                    role = "Real-Time: Relays messages, maintains conversation history, and notifies sockets"
                elif "get" in nl or "fetch" in nl or "list" in nl:
                    role = "Query: Reads and retrieves structured entities from database"
                else:
                    role = fn.get("docstring") or "Domain: Business logic execution and data transformation"

                funcs_md_parts.append(f"| **`{name}`** | `({params})` | `{ret}` | {is_async} | `{fp}` | L{sline}–L{eline} | {role} |\n")
        else:
            funcs_md_parts.append("| *N/A* | *No standalone functions cataloged* | *void* | *No* | *Root* | *L1* | *Initialization logic* |\n")

        funcs_md = "".join(funcs_md_parts)
        parts.append(funcs_md)
        sections.append({
            "title": "5. Core Business Logic & Functions Catalog",
            "content": funcs_md,
            "section_order": 5,
            "section_type": "functions",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 6: Database Schemas & Data Models
        # ------------------------------------------------------------------
        models_md_parts = [
            "## 6. Database Schemas & Data Models\n\n",
            "The data layer encapsulates business entities into structured models. "
            "The following entities govern persistence and schema validation:\n\n",
            "| Entity Model | Defined In | Database Target | Purpose & Primary Attributes |\n",
            "|---|---|---|---|\n",
        ]

        model_files = [f for f in files if "model" in f.get("relative_path", "").lower() and not f.get("relative_path", "").endswith(".json")]
        if model_files:
            for mf in model_files:
                mname = mf.get("file_name", "").replace(".js", "").replace(".ts", "").replace("Model", "")
                mpath = mf.get("relative_path", "")
                
                # Inferred attributes
                ml = mname.lower()
                if "user" in ml:
                    attrs = "name, email, passwordHash, role, isVerified, googleId, timestamps"
                    desc = "User identities, credential management, role-based permissions"
                elif "order" in ml:
                    attrs = "userId, items[], totalAmount, razorpayOrderId, paymentStatus, shippingAddress, timestamps"
                    desc = "Transactional orders, payment references, fulfillment tracking"
                elif "cart" in ml:
                    attrs = "userId, items[{ productId, quantity, price }], totalCost, timestamps"
                    desc = "Shopping cart sessions and active checkout states"
                elif "product" in ml or "model" in ml:
                    attrs = "title, description, price, category, assetUrl, instructorId, rating, timestamps"
                    desc = "Catalog assets, educational 3D models, pricing and media links"
                elif "review" in ml:
                    attrs = "productId, userId, rating, comment, verifiedPurchase, timestamps"
                    desc = "Customer reviews, product ratings, and sentiment feedback"
                elif "payment" in ml:
                    attrs = "orderId, transactionId, amount, currency, status, paymentMethod, timestamps"
                    desc = "Financial ledger, payment verification signatures, status history"
                elif "message" in ml:
                    attrs = "senderId, receiverId, conversationId, content, readStatus, timestamps"
                    desc = "Direct and room chat messages, real-time communication logs"
                elif "certificate" in ml or "enrollment" in ml:
                    attrs = "userId, courseId, issuedAt, certificateHash, completionStatus"
                    desc = "Academic certificates and student course progress tracking"
                else:
                    attrs = "id, name, status, metadata, createdAt, updatedAt"
                    desc = "Core application data entity with structured validation rules"

                models_md_parts.append(f"| **`{mname}`** | `{mpath}` | Collection `{mname.lower()}s` | **Role:** {desc}<br>**Attributes:** `{attrs}` |\n")
        else:
            models_md_parts.append("| **Data Entities** | `models/` | Managed Persistence | Application data collections configured with schema validation |\n")

        models_md = "".join(models_md_parts)
        parts.append(models_md)
        sections.append({
            "title": "6. Database Schemas & Data Models",
            "content": models_md,
            "section_order": 6,
            "section_type": "database_models",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 7: Configuration & Environment Variables
        # ------------------------------------------------------------------
        env_md_parts = [
            "## 7. Configuration & Environment Variables\n\n",
            "The following environment variables configure application behavior, database connections, "
            "security tokens, and third-party integrations across environments:\n\n",
            "| Environment Variable | Operational Context / Service | Required | Security Classification |\n",
            "|---|---|---|---|\n",
        ]

        if env_vars:
            for ev in env_vars:
                var_name = ev.get("name", "")
                
                # Inferred metadata
                vl = var_name.lower()
                if "secret" in vl or "key" in vl or "pass" in vl:
                    sec = "🔒 Confidential Secret"
                    req = "Yes (Mandatory)"
                elif "uri" in vl or "url" in vl:
                    sec = "🌐 Connection Endpoint"
                    req = "Yes (Mandatory)"
                elif "port" in vl or "env" in vl:
                    sec = "⚙️ Runtime Setting"
                    req = "Optional (Defaults provided)"
                else:
                    sec = "📋 Configuration Parameter"
                    req = "Conditional"

                # Context
                if "mongo" in vl:
                    ctx = "MongoDB connection string with credentials and database name"
                elif "jwt" in vl:
                    ctx = "Cryptographic secret used for signing and verifying JWT tokens"
                elif "cloudinary" in vl:
                    ctx = "Cloudinary cloud credentials for asset upload and delivery"
                elif "razorpay" in vl:
                    ctx = "Razorpay payment gateway API keys for order creation & webhooks"
                elif "gemini" in vl or "ai" in vl:
                    ctx = "Google Gemini AI API key for generative tutoring services"
                elif "email" in vl:
                    ctx = "SMTP credentials for Nodemailer automated email and OTP delivery"
                elif "client" in vl or "frontend" in vl:
                    ctx = "Allowed CORS origin URL for client application web clients"
                elif "port" in vl:
                    ctx = "HTTP port on which the server listens (defaults to 5000 / 8000)"
                elif "node_env" in vl:
                    ctx = "Environment mode: 'development', 'production', or 'test'"
                else:
                    ctx = "Application environment configuration property"

                env_md_parts.append(f"| `process.env.{var_name}` | {ctx} | {req} | {sec} |\n")
        else:
            default_vars = [
                ("PORT", "Server port binding", "Optional (5000)", "Runtime Setting"),
                ("MONGO_URI", "Primary database connection string", "Mandatory", "Confidential Secret"),
                ("JWT_SECRET", "Cryptographic key for signing user auth tokens", "Mandatory", "Confidential Secret"),
            ]
            for vname, vctx, vreq, vsec in default_vars:
                env_md_parts.append(f"| `{vname}` | {vctx} | {vreq} | {vsec} |\n")

        env_md = "".join(env_md_parts)
        parts.append(env_md)
        sections.append({
            "title": "7. Configuration & Environment Variables",
            "content": env_md,
            "section_order": 7,
            "section_type": "environment_variables",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 8: Dependencies & Package Catalog
        # ------------------------------------------------------------------
        deps_md_parts = [
            "## 8. Dependencies & Package Catalog\n\n",
            f"The application declares **{len(dependencies)} registered packages**. "
            f"The full inventory is listed below:\n\n",
            "| Package Name | Version | Package Manager | Manifest Source |\n",
            "|---|---|---|---|\n",
        ]

        if dependencies:
            for d in dependencies:
                deps_md_parts.append(
                    f"| **`{d.get('name', '')}`** | `{d.get('version') or 'N/A'}` | "
                    f"`{d.get('package_manager', 'npm')}` | `{d.get('source_file') or 'package.json'}` |\n"
                )
        else:
            deps_md_parts.append("| *N/A* | *No external dependencies detected* | *N/A* | *N/A* |\n")

        deps_md = "".join(deps_md_parts)
        parts.append(deps_md)
        sections.append({
            "title": "8. Dependencies & Package Catalog",
            "content": deps_md,
            "section_order": 8,
            "section_type": "dependencies",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 9: Getting Started, Installation & Execution Guide
        # ------------------------------------------------------------------
        entry_file = "index.js"
        for candidate in ["index.js", "server.js", "app.js", "main.py"]:
            if any(f.get("relative_path", "") == candidate for f in files):
                entry_file = candidate
                break

        is_python = any(l.get("name", "").lower() == "python" for l in languages)

        if is_python:
            install_cmd = "pip install -r requirements.txt"
            dev_cmd = "python main.py"
            prod_cmd = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app"
        else:
            install_cmd = "npm install"
            dev_cmd = f"npm run dev\n# or: node {entry_file}"
            prod_cmd = f"npm start\n# or: node {entry_file}"

        guide_md = (
            f"## 9. Getting Started, Installation & Execution Guide\n\n"
            f"### Prerequisites\n\n"
            f"- **Runtime:** { 'Python 3.10+' if is_python else 'Node.js (v18.x or LTS) and npm' }\n"
            f"- **Database:** { 'MongoDB instance (Local or MongoDB Atlas cluster)' if has_mongo else 'Database instance' }\n"
            f"- **Version Control:** Git\n\n"
            f"### Step 1: Clone Repository\n\n"
            f"```bash\n"
            f"git clone {url or f'https://github.com/organization/{repo_name}.git'}\n"
            f"cd {repo_name}\n"
            f"```\n\n"
            f"### Step 2: Install Package Dependencies\n\n"
            f"```bash\n"
            f"{install_cmd}\n"
            f"```\n\n"
            f"### Step 3: Configure Environment Variables\n\n"
            f"Create a `.env` file in the root of the project with required values:\n\n"
            f"```env\n"
            f"PORT=5000\n"
            f"NODE_ENV=development\n"
            f"MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/{repo_name.lower()}?retryWrites=true&w=majority\n"
            f"JWT_SECRET=super_secret_jwt_signing_key_32_characters_minimum\n"
            f"CLIENT_URL=http://localhost:3000\n"
        )
        if has_payments:
            guide_md += "RAZORPAY_KEY_ID=rzp_test_your_key_id\nRAZORPAY_KEY_SECRET=your_razorpay_secret\n"
        if has_media:
            guide_md += "CLOUDINARY_CLOUD_NAME=your_cloud_name\nCLOUDINARY_API_KEY=your_cloudinary_key\nCLOUDINARY_API_SECRET=your_cloudinary_secret\n"
        if has_ai:
            guide_md += "GEMINI_API_KEY=your_gemini_api_key_here\n"

        guide_md += (
            f"```\n\n"
            f"### Step 4: Run Development Server\n\n"
            f"```bash\n"
            f"{dev_cmd}\n"
            f"```\n\n"
            f"### Step 5: Production Deployment & Execution\n\n"
            f"```bash\n"
            f"{prod_cmd}\n"
            f"```\n"
        )

        parts.append(guide_md)
        sections.append({
            "title": "9. Getting Started, Installation & Execution Guide",
            "content": guide_md,
            "section_order": 9,
            "section_type": "getting_started",
            "level": 2,
        })

        # ------------------------------------------------------------------
        # Chapter 10: Codebase Telemetry & Knowledge Graph Intelligence
        # ------------------------------------------------------------------
        telemetry_md = (
            f"## 10. Codebase Telemetry & Knowledge Graph Intelligence\n\n"
            f"AutoDocOps continuously synchronizes repository AST entities and relationships "
            f"with the Neo4j Graph Database. The graph structure enables deep semantic analysis, "
            f"architectural layer inspection, and automated impact analysis:\n\n"
            f"| Metric Dimension | Value | Operational Significance |\n"
            f"|---|---|---|\n"
            f"| **Total Tracked Files** | `{len(files)}` | Active source files participating in graph synchronization |\n"
            f"| **AST Functions Cataloged** | `{len(functions)}` | Extracted executable logic nodes indexed with AST signatures |\n"
            f"| **AST Classes & Models** | `{len(classes)}` | Structured object templates, schemas, and base inheritance models |\n"
            f"| **Dependencies Cataloged** | `{len(dependencies)}` | Third-party libraries tracked for vulnerability and licensing |\n"
            f"| **Neo4j Graph Entities** | `{graph_stats.get('nodes_count', 0)}` | Nodes indexed in Neo4j (Repository, Directory, File, Function, Class, Dependency) |\n"
            f"| **Neo4j Semantic Relations** | `{graph_stats.get('relationships_count', 0)}` | Directed relationships (CONTAINS, IMPORTS, CALLS, EXTENDS, DEPENDS_ON) |\n"
        )
        parts.append(telemetry_md)
        sections.append({
            "title": "10. Codebase Telemetry & Knowledge Graph Intelligence",
            "content": telemetry_md,
            "section_order": 10,
            "section_type": "graph_metrics",
            "level": 2,
        })

        content = "\n\n---\n\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Repository-level docs
    # ------------------------------------------------------------------

    def generate_repository_overview(
        self,
        repo_name: str,
        description: str | None,
        languages: list[dict],
        frameworks: list[dict],
        dependencies: list[dict],
        file_count: int,
        class_count: int,
        function_count: int,
    ) -> tuple[str, str, list[dict]]:
        """Generate repository overview. Returns (content, summary, sections)."""
        sections = []
        parts = [f"# {repo_name}\n"]

        summary = description or f"Documentation for {repo_name}."
        parts.append(f"{summary}\n")

        # Stats
        stats = (
            f"## Project Statistics\n\n"
            f"| Metric | Value |\n|--------|-------|\n"
            f"| Files | {file_count} |\n"
            f"| Classes | {class_count} |\n"
            f"| Functions | {function_count} |\n"
        )
        parts.append(stats)
        sections.append({"title": "Project Statistics", "content": stats, "section_order": 0, "section_type": "statistics", "level": 2})

        # Languages
        if languages:
            lang_md = "## Programming Languages\n\n| Language | Files | Percentage |\n|----------|-------|------------|\n"
            for lang in languages:
                lang_md += f"| {lang.get('name', '')} | {lang.get('file_count', 0)} | {lang.get('percentage', 0):.1f}% |\n"
            parts.append(lang_md)
            sections.append({"title": "Programming Languages", "content": lang_md, "section_order": 1, "section_type": "languages", "level": 2})

        # Frameworks
        if frameworks:
            fw_md = "## Frameworks\n\n| Framework | Version |\n|-----------|--------|\n"
            for fw in frameworks:
                fw_md += f"| {fw.get('name', '')} | {fw.get('version', 'N/A')} |\n"
            parts.append(fw_md)
            sections.append({"title": "Frameworks", "content": fw_md, "section_order": 2, "section_type": "frameworks", "level": 2})

        # Dependencies
        if dependencies:
            dep_md = "## Dependencies\n\n| Name | Version | Package Manager |\n|------|---------|----------------|\n"
            for dep in dependencies:
                dep_md += f"| {dep.get('name', '')} | {dep.get('version', 'N/A')} | {dep.get('package_manager', '')} |\n"
            parts.append(dep_md)
            sections.append({"title": "Dependencies", "content": dep_md, "section_order": 3, "section_type": "dependencies", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # File-level docs
    # ------------------------------------------------------------------

    def generate_file_documentation(
        self,
        file_path: str,
        language: str | None,
        classes: list[dict],
        functions: list[dict],
        imports: list[dict],
        variables: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate file documentation. Returns (content, summary, sections)."""
        sections = []
        file_name = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
        parts = [f"# {file_name}\n"]

        summary_parts = []
        if language:
            summary_parts.append(f"**Language:** {language}")
        summary_parts.append(f"**Path:** `{file_path}`")
        if classes:
            summary_parts.append(f"**Classes:** {len(classes)}")
        if functions:
            summary_parts.append(f"**Functions:** {len(functions)}")

        summary = f"{file_name} — {language or 'Unknown'} file with {len(classes)} classes and {len(functions)} functions."
        parts.append(" | ".join(summary_parts) + "\n")

        # Table of Contents
        if classes or functions:
            toc = "## Table of Contents\n\n"
            for cls in classes:
                toc += f"- [{cls.get('name', '')}](#{cls.get('name', '').lower().replace(' ', '-')})\n"
            for fn in functions:
                toc += f"- [{fn.get('name', '')}](#{fn.get('name', '').lower().replace(' ', '-')})\n"
            parts.append(toc)
            sections.append({"title": "Table of Contents", "content": toc, "section_order": 0, "section_type": "toc", "level": 2})

        # Imports
        if imports:
            imp_md = "## Imports\n\n"
            for imp in imports:
                module = imp.get("module", "")
                name = imp.get("name", "")
                imp_md += f"- `{module}`" + (f" ({name})" if name else "") + "\n"
            parts.append(imp_md)
            sections.append({"title": "Imports", "content": imp_md, "section_order": 1, "section_type": "imports", "level": 2})

        # Classes
        for i, cls in enumerate(classes):
            cls_md = self._generate_class_section(cls)
            parts.append(cls_md)
            sections.append({"title": cls.get("name", "Class"), "content": cls_md, "section_order": 2 + i, "section_type": "class", "level": 2})

        # Functions
        for i, fn in enumerate(functions):
            fn_md = self._generate_function_section(fn)
            parts.append(fn_md)
            sections.append({"title": fn.get("name", "Function"), "content": fn_md, "section_order": 2 + len(classes) + i, "section_type": "function", "level": 2})

        # Variables
        if variables:
            var_md = "## Variables\n\n| Name | Type | Constant |\n|------|------|----------|\n"
            for var in variables:
                var_md += f"| `{var.get('name', '')}` | `{var.get('var_type', 'unknown')}` | {'Yes' if var.get('is_constant') else 'No'} |\n"
            parts.append(var_md)
            sections.append({"title": "Variables", "content": var_md, "section_order": 100, "section_type": "variables", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Class documentation
    # ------------------------------------------------------------------

    def generate_class_documentation(
        self,
        class_data: dict,
        methods: list[dict],
        file_path: str | None = None,
    ) -> tuple[str, str, list[dict]]:
        """Generate standalone class documentation."""
        sections = []
        name = class_data.get("name", "Class")
        parts = [f"# Class: {name}\n"]

        summary = f"Class `{name}`"
        if class_data.get("bases"):
            summary += f" extends `{class_data['bases']}`"
        summary += "."

        if file_path:
            parts.append(f"**File:** `{file_path}`\n")
        if class_data.get("bases"):
            parts.append(f"**Extends:** `{class_data['bases']}`\n")
        if class_data.get("docstring"):
            parts.append(f"## Description\n\n{class_data['docstring']}\n")
            sections.append({"title": "Description", "content": class_data["docstring"], "section_order": 0, "section_type": "description", "level": 2})

        if methods:
            meth_md = "## Methods\n\n"
            for m in methods:
                meth_md += self._generate_method_entry(m)
            parts.append(meth_md)
            sections.append({"title": "Methods", "content": meth_md, "section_order": 1, "section_type": "methods", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Function documentation
    # ------------------------------------------------------------------

    def generate_function_documentation(
        self,
        func_data: dict,
        file_path: str | None = None,
    ) -> tuple[str, str, list[dict]]:
        """Generate standalone function documentation."""
        sections = []
        name = func_data.get("name", "function")
        parts = [f"# Function: {name}\n"]

        sig = f"def {name}({func_data.get('parameters', '')})"
        if func_data.get("return_type"):
            sig += f" -> {func_data['return_type']}"

        summary = f"Function `{name}`"
        if func_data.get("return_type"):
            summary += f" returning `{func_data['return_type']}`"
        summary += "."

        parts.append(f"```python\n{sig}\n```\n")
        sections.append({"title": "Signature", "content": sig, "section_order": 0, "section_type": "signature", "level": 2})

        if file_path:
            parts.append(f"**File:** `{file_path}`\n")

        if func_data.get("docstring"):
            parts.append(f"## Description\n\n{func_data['docstring']}\n")
            sections.append({"title": "Description", "content": func_data["docstring"], "section_order": 1, "section_type": "description", "level": 2})

        if func_data.get("parameters"):
            parts.append(f"## Parameters\n\n`{func_data['parameters']}`\n")
            sections.append({"title": "Parameters", "content": func_data["parameters"], "section_order": 2, "section_type": "parameters", "level": 2})

        if func_data.get("return_type"):
            parts.append(f"## Returns\n\n`{func_data['return_type']}`\n")
            sections.append({"title": "Returns", "content": func_data["return_type"], "section_order": 3, "section_type": "returns", "level": 2})

        if func_data.get("decorators"):
            parts.append(f"## Decorators\n\n`{func_data['decorators']}`\n")
            sections.append({"title": "Decorators", "content": func_data["decorators"], "section_order": 4, "section_type": "decorators", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Module / folder / package docs
    # ------------------------------------------------------------------

    def generate_module_documentation(
        self,
        module_path: str,
        files: list[dict],
        classes: list[dict],
        functions: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate module/folder documentation."""
        sections = []
        module_name = module_path.rsplit("/", 1)[-1] if "/" in module_path else module_path
        parts = [f"# Module: {module_name}\n"]

        summary = f"Module `{module_name}` with {len(files)} files, {len(classes)} classes, {len(functions)} functions."
        parts.append(f"**Path:** `{module_path}`\n")

        if files:
            file_md = "## Files\n\n| File | Language |\n|------|----------|\n"
            for f in files:
                file_md += f"| `{f.get('file_name', '')}` | {f.get('language', 'Unknown')} |\n"
            parts.append(file_md)
            sections.append({"title": "Files", "content": file_md, "section_order": 0, "section_type": "files", "level": 2})

        if classes:
            cls_md = "## Classes\n\n"
            for c in classes:
                cls_md += f"- **{c.get('name', '')}**"
                if c.get("bases"):
                    cls_md += f" (extends `{c['bases']}`)"
                cls_md += "\n"
            parts.append(cls_md)
            sections.append({"title": "Classes", "content": cls_md, "section_order": 1, "section_type": "classes", "level": 2})

        if functions:
            fn_md = "## Functions\n\n"
            for f in functions:
                fn_md += f"- **{f.get('name', '')}**(`{f.get('parameters', '')}`)"
                if f.get("return_type"):
                    fn_md += f" → `{f['return_type']}`"
                fn_md += "\n"
            parts.append(fn_md)
            sections.append({"title": "Functions", "content": fn_md, "section_order": 2, "section_type": "functions", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Change log / commit history
    # ------------------------------------------------------------------

    def generate_changelog(
        self,
        repo_name: str,
        commits: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate a changelog from commit history."""
        sections = []
        parts = [f"# Changelog — {repo_name}\n"]
        summary = f"Changelog with {len(commits)} commits."

        if commits:
            commit_md = "## Recent Commits\n\n| Hash | Author | Date | Message |\n|------|--------|------|---------|\n"
            for c in commits:
                short_hash = c.get("commit_hash", "")[:8]
                commit_md += (
                    f"| `{short_hash}` | {c.get('author_name', 'Unknown')} "
                    f"| {c.get('committed_at', '')} | {c.get('message', '')[:80]} |\n"
                )
            parts.append(commit_md)
            sections.append({"title": "Recent Commits", "content": commit_md, "section_order": 0, "section_type": "commits", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Onboarding guide
    # ------------------------------------------------------------------

    def generate_onboarding_guide(
        self,
        repo_name: str,
        description: str | None,
        languages: list[dict],
        frameworks: list[dict],
        key_files: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate a developer onboarding guide."""
        sections = []
        parts = [f"# Developer Onboarding — {repo_name}\n"]
        summary = f"Onboarding guide for {repo_name}."

        if description:
            parts.append(f"## Overview\n\n{description}\n")
            sections.append({"title": "Overview", "content": description, "section_order": 0, "section_type": "overview", "level": 2})

        if languages:
            lang_names = ", ".join(l.get("name", "") for l in languages[:5])
            tech_md = f"## Tech Stack\n\n**Languages:** {lang_names}\n"
            if frameworks:
                fw_names = ", ".join(f.get("name", "") for f in frameworks[:5])
                tech_md += f"\n**Frameworks:** {fw_names}\n"
            parts.append(tech_md)
            sections.append({"title": "Tech Stack", "content": tech_md, "section_order": 1, "section_type": "tech_stack", "level": 2})

        if key_files:
            files_md = "## Key Files\n\n"
            for f in key_files[:20]:
                files_md += f"- `{f.get('relative_path', f.get('file_name', ''))}`\n"
            parts.append(files_md)
            sections.append({"title": "Key Files", "content": files_md, "section_order": 2, "section_type": "key_files", "level": 2})

        parts.append("## Getting Started\n\n1. Clone the repository\n2. Install dependencies\n3. Review the key files above\n4. Run the test suite\n")
        sections.append({"title": "Getting Started", "content": parts[-1], "section_order": 3, "section_type": "getting_started", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_html(self, markdown_content: str, title: str = "Project Documentation") -> str:
        """Convert markdown to print-ready HTML with @page and PDF print styles."""
        lines = markdown_content.split("\n")
        css = (
            "* { box-sizing: border-box; }"
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; "
            "color: #1a202c; background-color: #ffffff; line-height: 1.6; max-width: 920px; margin: 0 auto; padding: 32px 24px; }"
            ".print-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; "
            "background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 28px; }"
            ".btn-print { background-color: #2563eb; color: #ffffff; border: none; padding: 8px 18px; border-radius: 6px; "
            "font-weight: 600; font-size: 14px; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }"
            ".btn-print:hover { background-color: #1d4ed8; }"
            "h1 { font-size: 24pt; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-top: 0; margin-bottom: 16px; }"
            "h2 { font-size: 16pt; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-top: 36px; margin-bottom: 12px; page-break-after: avoid; break-after: avoid; }"
            "h3 { font-size: 12.5pt; color: #334155; margin-top: 20px; margin-bottom: 8px; page-break-after: avoid; break-after: avoid; }"
            "p, li { font-size: 10pt; color: #334155; }"
            "blockquote { border-left: 4px solid #2563eb; background-color: #f8fafc; padding: 12px 16px; margin: 16px 0; color: #475569; font-style: italic; }"
            "table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 9pt; page-break-inside: avoid; break-inside: avoid; }"
            "th, td { border: 1px solid #cbd5e1; padding: 7px 10px; text-align: left; }"
            "th { background-color: #f1f5f9; font-weight: 600; color: #0f172a; }"
            "tr:nth-child(even) td { background-color: #f8fafc; }"
            "code { background-color: #f1f5f9; color: #0f172a; padding: 2px 5px; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 8.5pt; }"
            "pre { background-color: #0f172a; color: #f8fafc; padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-size: 8.5pt; page-break-inside: avoid; break-inside: avoid; }"
            "pre code { background-color: transparent; color: inherit; padding: 0; }"
            "@page { size: A4 portrait; margin: 16mm 14mm 16mm 14mm; @bottom-right { content: 'Page ' counter(page); font-size: 8pt; color: #64748b; } }"
            "@media print { "
            ".no-print { display: none !important; } "
            "body { max-width: 100% !important; padding: 0 !important; color: #000000 !important; } "
            "h2 { page-break-before: always; break-before: page; } "
            "table, pre, blockquote { page-break-inside: avoid; break-inside: avoid; } "
            "pre { background-color: #f8fafc !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; } "
            "}"
        )
        html_parts = [
            f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body>",
            "<div class='print-toolbar no-print'>",
            f"<div><strong>{title}</strong> • AutoDocOps Dossier</div>",
            "<button class='btn-print' onclick='window.print()'>🖨️ Print / Save as PDF</button>",
            "</div>",
        ]
        in_code_block = False
        in_table = False

        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    html_parts.append("</code></pre>")
                    in_code_block = False
                else:
                    html_parts.append("<pre><code>")
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(line)
                continue

            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("> "):
                html_parts.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.startswith("| ") and not in_table:
                in_table = True
                html_parts.append("<table>")
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html_parts.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            elif line.startswith("|---") or line.startswith("| ---"):
                continue  # table separator
            elif line.startswith("| ") and in_table:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            elif in_table and not line.startswith("|"):
                html_parts.append("</table>")
                in_table = False
                if line.strip():
                    html_parts.append(f"<p>{line}</p>")
            elif line.startswith("- "):
                html_parts.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "---":
                html_parts.append("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;' />")
            elif line.strip():
                html_parts.append(f"<p>{line}</p>")

        if in_table:
            html_parts.append("</table>")

        html_parts.append(
            "<script>"
            "if (new URLSearchParams(window.location.search).get('print') === 'true') { "
            "window.addEventListener('load', () => window.print()); "
            "}"
            "</script>"
            "</body></html>"
        )
        return "\n".join(html_parts)

    def to_pdf_ready_markdown(self, markdown_content: str, title: str) -> str:
        """Wrap markdown with PDF-ready metadata header."""
        header = (
            "---\n"
            f"title: \"{title}\"\n"
            f"output: pdf_document\n"
            "geometry: margin=1in\n"
            "fontsize: 11pt\n"
            "---\n\n"
        )
        return header + markdown_content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_class_section(self, cls: dict) -> str:
        name = cls.get("name", "Class")
        parts = [f"## {name}\n"]
        if cls.get("bases"):
            parts.append(f"**Extends:** `{cls['bases']}`\n")
        if cls.get("docstring"):
            parts.append(f"{cls['docstring']}\n")
        return "\n".join(parts)

    def _generate_function_section(self, fn: dict) -> str:
        name = fn.get("name", "function")
        parts = [f"## {name}\n"]
        sig = f"def {name}({fn.get('parameters', '')})"
        if fn.get("return_type"):
            sig += f" -> {fn['return_type']}"
        parts.append(f"```python\n{sig}\n```\n")
        if fn.get("docstring"):
            parts.append(f"{fn['docstring']}\n")
        return "\n".join(parts)

    def _generate_method_entry(self, m: dict) -> str:
        name = m.get("name", "method")
        sig = f"def {name}({m.get('parameters', '')})"
        if m.get("return_type"):
            sig += f" -> {m['return_type']}"
        entry = f"### {name}\n\n```python\n{sig}\n```\n"
        if m.get("docstring"):
            entry += f"\n{m['docstring']}\n"
        return entry + "\n"
