import type { Translations } from "./en";

/**
 * Hindi (हिंदी).
 *
 * Written for a Hindi-speaking technical operator, not translated word for
 * word. Two deliberate conventions:
 *
 * 1. Globally recognised technical product terms stay in English or in their
 *    standard Devanagari transliteration — API, JSON, OAuth, MCP, Redis,
 *    PostgreSQL, डैशबोर्ड, वर्कफ़्लो, रनटाइम. Forcing a "pure" Hindi coinage
 *    for these makes the interface harder to use, not more local.
 * 2. One product concept gets exactly one Hindi word everywhere. Tasks are
 *    always कार्य, approvals always स्वीकृति, memory always मेमोरी.
 *
 * Typed as Translations, so omitting or misspelling any key fails typecheck
 * rather than silently rendering a raw key to a user.
 */
export const hi: Translations = {
  common: {
    save: "सहेजें",
    cancel: "रद्द करें",
    close: "बंद करें",
    delete: "हटाएँ",
    retry: "पुनः प्रयास करें",
    refresh: "रिफ़्रेश करें",
    viewAll: "सभी देखें",
    search: "खोजें",
    loading: "लोड हो रहा है…",
    signIn: "साइन इन करें",
    authenticate: "प्रमाणित करें",
    unavailable: "अनुपलब्ध",
    offline: "ऑफ़लाइन",
    noAccess: "पहुँच नहीं",
    yes: "हाँ",
    no: "नहीं",
    optional: "वैकल्पिक",
    required: "आवश्यक",
    copy: "कॉपी करें",
    copied: "कॉपी हो गया",
    back: "वापस",
    next: "आगे",
    done: "पूर्ण",
    allOutcomes: "सभी परिणाम",
    allScopes: "सभी स्कोप",
    allIntegrations: "सभी इंटीग्रेशन",
    success: "सफल",
    failed: "विफल",
    approvalRequired: "स्वीकृति आवश्यक",
    selectTool: "कोई टूल चुनें…",
    approvedBy: "स्वीकृतकर्ता",
    sessionGrants: "इस सत्र के अनुदान",
    sessionTasks: "इस सत्र के कार्य",
    events: "घटनाएँ",
    priorityLow: "कम",
    priorityNormal: "सामान्य",
    priorityHigh: "उच्च",
    priorityCritical: "अत्यावश्यक",
    notConfigured: "कॉन्फ़िगर नहीं",
    saveConfiguration: "कॉन्फ़िगरेशन सहेजें",
    appearance: "रूप",
    about: "परिचय",
    displayName: "प्रदर्शित नाम",
    none: "कोई नहीं",
    executionStages: "निष्पादन चरण",
    finalAnswer: "अंतिम उत्तर",
    finalSynthesis: "अंतिम संश्लेषण",
    reviewerIssues: "समीक्षक टिप्पणियाँ",
    autonomousSpecialists: "स्वायत्त specialists",
    resumePausedSteps: "रुके हुए स्टेप फिर से शुरू करें",
    idempotencyKey: "Idempotency कुंजी",
  },

  language: {
    label: "भाषा",
    switchTo: "{language} पर स्विच करें",
    current: "वर्तमान भाषा: {language}",
  },

  theme: {
    label: "थीम",
    change: "थीम बदलें",
    dark: "डार्क",
    light: "लाइट",
    system: "सिस्टम",
  },

  nav: {
    groups: {
      overview: "अवलोकन",
      execution: "निष्पादन",
      workflows: "वर्कफ़्लो",
      knowledge: "ज्ञान",
      operations: "संचालन",
      system: "सिस्टम",
    },
    items: {
      dashboard: "डैशबोर्ड",
      productOverview: "उत्पाद अवलोकन",
      tasks: "कार्य",
      orchestrate: "ऑर्केस्ट्रेट",
      autonomousRuns: "स्वायत्त रन",
      agents: "एजेंट",
      workflows: "वर्कफ़्लो",
      workflowRuns: "वर्कफ़्लो रन",
      approvals: "स्वीकृतियाँ",
      memory: "मेमोरी",
      runtime: "रनटाइम",
      tools: "टूल",
      integrations: "इंटीग्रेशन",
      auditLogs: "ऑडिट लॉग",
      health: "सिस्टम स्वास्थ्य",
      settings: "सेटिंग्स",
      privacy: "गोपनीयता और नीति",
    },
    openNavigation: "नेविगेशन खोलें",
    expandSidebar: "साइडबार विस्तृत करें",
    collapseSidebar: "साइडबार संक्षिप्त करें",
  },

  topbar: {
    searchPlaceholder: "खोजें या जाएँ…",
    apiOnline: "API ऑनलाइन",
    apiOffline: "API ऑफ़लाइन",
    connecting: "कनेक्ट हो रहा है",
    degraded: "सीमित",
    keyNeeded: "कुंजी आवश्यक",
    checkingApi: "API की जाँच हो रही है…",
    apiUnreachable: "API तक नहीं पहुँच सके। सेटिंग्स में बेस URL जाँचें।",
    storageEphemeral: "स्टोरेज अस्थायी है — API पुनः आरंभ होने पर डेटा मिट जाता है।",
    nonProduction: "गैर-प्रोडक्शन परिनियोजन ({environment})",
  },

  states: {
    loading: "लोड हो रहा है…",
    nothingYet: "इस सत्र में अभी कुछ नहीं।",
    somethingWentWrong: "कुछ गड़बड़ हो गई",
    unexpectedError: "अप्रत्याशित त्रुटि",
    timedOut: "अनुरोध का समय समाप्त हो गया",
    cantReachApi: "API तक नहीं पहुँच सके",
    networkHint: "अपना नेटवर्क या API कॉन्फ़िगरेशन जाँचें।",
    tried: "प्रयास किया: {url}",
    notFound: "नहीं मिला",
    authRequiredTitle: "ऑपरेटर प्रमाणीकरण आवश्यक",
    authRequiredBody: "प्रमाणीकरण के बाद यह दृश्य उपलब्ध होगा — {detail}",
    serviceUnavailableTitle: "सेवा अस्थायी रूप से अनुपलब्ध",
    permissionDeniedTitle: "अनुमति अस्वीकृत",
    correlationId: "कोरिलेशन ID: {id}",
  },

  errorCodes: {
    auth_not_configured: "इस परिनियोजन में कोई ऑपरेटर कुंजी कॉन्फ़िगर नहीं है।",
    authentication_required: "जारी रखने के लिए ऑपरेटर कुंजी से साइन इन करें।",
    authentication_invalid: "वह ऑपरेटर कुंजी स्वीकार नहीं की गई।",
  },

  dashboard: {
    apiStatus: "API स्थिति",
    online: "ऑनलाइन",
    offline: "ऑफ़लाइन",
    degraded: "सीमित",
    toolsAvailable: "उपलब्ध टूल",
    auditEvents: "ऑडिट घटनाएँ",
    thisSession: "यह सत्र",
    sessionHint: "यहाँ आरंभ किए गए कार्य, रन और निष्पादन",
    ephemeralHint: "अस्थायी स्टोरेज — पुनः आरंभ पर डेटा मिट जाता है",
    keyRequiredToList: "{action} के लिए ऑपरेटर कुंजी आवश्यक",
    notPermittedTo: "इस कुंजी को {action} की अनुमति नहीं है",
    actionListTools: "टूल सूचीबद्ध करने",
    actionReadAudit: "ऑडिट लॉग पढ़ने",
    recentAudit: "हालिया ऑडिट गतिविधि",
    noAuditYet: "अभी तक कोई ऑडिट घटना नहीं",
    auditHint: "टूल निष्पादन और स्वीकृति जाँच यहाँ दिखाई देंगी।",
    quickActions: "त्वरित कार्रवाइयाँ",
    startOrchestration: "ऑर्केस्ट्रेशन आरंभ करें",
    runAutonomous: "स्वायत्त उद्देश्य चलाएँ",
    createTask: "कार्य बनाएँ",
    sessionActivity: "सत्र गतिविधि",
    tasks: "कार्य",
    workflowRuns: "वर्कफ़्लो रन",
    runtimeExecutions: "रनटाइम निष्पादन",
    view: "देखें",
  },

  pages: {
    overview: {
      title: "उत्पाद अवलोकन",
      heroTitle: "एक एजेंट प्लेटफ़ॉर्म जो पहले सोचता है, फिर आपके नियंत्रण में कार्य करता है।",
      whatItDoes: "यह क्या करता है",
      everyItemLinks: "हर आइटम लाइव सतह से जुड़ा है",
      howItStaysTrustworthy: "यह भरोसेमंद कैसे रहता है",
      trustworthyBody:
        "स्वायत्तता तभी उपयोगी है जब उसकी सीमाएँ हों। ये सीमाएँ कोड में लागू हैं, किसी नीति दस्तावेज़ में लिखी हुई नहीं।",
      startOrchestration: "ऑर्केस्ट्रेशन आरंभ करें",
      browseConnectors: "कनेक्टर देखें",
      connectors: "कनेक्टर",
      viewIntegrations: "इंटीग्रेशन देखें",
    },
    tasks: {
      title: "कार्य",
      description:
        "कार्य बनाएँ और उन्हें ID से खोजें। API कार्यों की सूची नहीं देता, इसलिए इस सत्र के हालिया कार्य नीचे दिखाए गए हैं।",
      lookupPlaceholder: "कार्य ID चिपकाएँ",
      emptyTitle: "अभी तक कोई कार्य नहीं बनाया गया",
      emptyBody: "ऊपर बनाए गए कार्य यहाँ त्वरित खोज के लिए दिखाई देंगे।",
    },
    orchestrate: {
      title: "ऑर्केस्ट्रेट",
      description:
        "एक ही उद्देश्य पर researcher → builder → reviewer मल्टी-एजेंट ऑर्केस्ट्रेशन चलाएँ।",
      objectivePlaceholder: "नई बिलिंग प्रणाली के लिए रोलआउट योजना बनाएँ",
      contextPlaceholder: "प्रासंगिक बाधाएँ, पूर्व निर्णय, या पृष्ठभूमि",
      working: "Researcher, builder और reviewer काम कर रहे हैं…",
      emptyTitle: "अभी तक कोई ऑर्केस्ट्रेशन रन नहीं",
      emptyBody:
        "ऊपर एक उद्देश्य दर्ज करें और चलाएँ, फिर researcher, builder और reviewer की गतिविधि देखें।",
    },
    autonomous: {
      title: "स्वायत्त रन",
      description:
        "Planner → specialist jobs → verifier → synthesis — एक ही उद्देश्य से पूरी तरह स्वायत्त।",
      working: "योजना, specialist निष्पादन और सत्यापन जारी…",
      emptyTitle: "अभी तक कोई स्वायत्त रन नहीं",
      emptyBody: "ऊपर एक उद्देश्य भेजें और planner, specialists तथा verifier को काम करते देखें।",
    },
    agents: {
      title: "एजेंट",
      description:
        "THYNACT प्रति ऑर्केस्ट्रेशन तीन निश्चित भूमिकाएँ चलाता है, और प्रति स्वायत्त रन गतिशील रूप से नामित specialists।",
    },
    workflowRuns: {
      title: "वर्कफ़्लो रन",
      description:
        "ID से रन देखें और स्वीकृति ठहराव के बाद उसे फिर से शुरू करें। API रन सूची नहीं देता, इसलिए इस सत्र के रन नीचे दिखाए गए हैं।",
      lookupPlaceholder: "वर्कफ़्लो रन ID चिपकाएँ",
      approvalIdPlaceholder: "स्वीकृति ID",
      emptyTitle: "अभी तक कोई वर्कफ़्लो रन नहीं",
      emptyBody: "वर्कफ़्लो एडिटर से आरंभ किए गए रन यहाँ दिखाई देंगे।",
    },
    approvals: {
      title: "स्वीकृति केंद्र",
      description:
        "THYNACT लंबित अनुरोध कतार के बजाय एकल-उपयोग, पूर्व-अधिकृत स्वीकृति अनुदान का उपयोग करता है।",
      emptyTitle: "अभी तक कोई स्वीकृति जारी नहीं",
      emptyBody: "ऊपर जारी किए गए अनुदान यहाँ सूचीबद्ध होंगे, टूल पेज पर पुनः उपयोग के लिए।",
    },
    memory: {
      title: "मेमोरी",
      description: "THYNACT की सिमेंटिक + लेक्सिकल मेमोरी खोजें, या सीधे नई मेमोरी लिखें।",
      searchHint: "सिमेंटिक + लेक्सिकल प्रासंगिकता के अनुसार क्रमित",
      listView: "सूची दृश्य",
      graphView: "ग्राफ़ दृश्य",
      emptyTitle: "कोई मेमोरी नहीं मिली",
      emptyBody: "कोई दूसरी क्वेरी या स्कोप आज़माएँ।",
      deleteMemory: "मेमोरी हटाएँ",
      deleteTitle: "यह मेमोरी हटाएँ?",
      deleteBody: "इसे पूर्ववत नहीं किया जा सकता।",
    },
    runtime: {
      title: "रनटाइम",
      description:
        "प्रदाता-समर्थित वर्कफ़्लो चलाएँ — पुनःप्रयास, idempotency और कोरिलेशन ट्रैकिंग के साथ।",
      lookupPlaceholder: "निष्पादन ID चिपकाएँ",
      emptyTitle: "अभी तक कोई निष्पादन आरंभ नहीं हुआ",
    },
    tools: {
      title: "टूल",
      description:
        "टूल रजिस्ट्री देखें, write/high-risk टूल के लिए विश्वसनीय (एकल-उपयोग) स्वीकृति जारी करें, और उन्हें सुरक्षित रूप से चलाएँ।",
      emptyTitle: "कोई टूल पंजीकृत नहीं",
      approvalPlaceholder: "write/high-risk टूल के लिए आवश्यक",
      executing: "चल रहा है…",
    },
    integrations: {
      title: "THYNACT इंटीग्रेशन",
      description: "बुद्धिमत्ता को उन टूल से जोड़ें जो काम पूरा करते हैं।",
      emptyTitle: "अभी तक कोई इंटीग्रेशन कनेक्ट नहीं है।",
      emptyBody: "नीचे से कोई कनेक्ट करें, या आरंभ करने के लिए MCP सर्वर जोड़ें।",
      searchPlaceholder: "इंटीग्रेशन खोजें…",
      noMatchTitle: "आपकी खोज से कोई इंटीग्रेशन मेल नहीं खाता",
      noMatchBody: "कोई दूसरा शब्द आज़माएँ या फ़िल्टर हटाएँ।",
      addMcpServer: "MCP सर्वर जोड़ें",
      currentlyIntegrated: "वर्तमान में इंटीग्रेटेड",
      readyToConnect: "कनेक्ट के लिए तैयार",
      comingSoon: "जल्द आ रहा है",
      all: "सभी",
      connected: "कनेक्टेड",
      operatorAccessRequired:
        "इंटीग्रेशन कनेक्ट, कॉन्फ़िगर या टेस्ट करने के लिए ऑपरेटर पहुँच आवश्यक है — नीचे दी गई सूची फिर भी देखी जा सकती है।",
    },
    audit: {
      title: "ऑडिट लॉग",
      description: "हर टूल निष्पादन और स्वीकृति जाँच, सबसे नया पहले।",
      filterPlaceholder: "टूल से फ़िल्टर करें…",
      tableView: "तालिका दृश्य",
      timelineView: "टाइमलाइन दृश्य",
      emptyTitle: "कोई मेल खाती ऑडिट घटना नहीं",
      auditEvent: "ऑडिट घटना",
      copyCorrelationId: "कोरिलेशन ID कॉपी करें",
    },
    health: {
      title: "सिस्टम स्वास्थ्य",
      description: "बैकएंड के /health और /ready एंडपॉइंट से सीधा लाइव स्टेटस।",
      status: "स्थिति",
      service: "सेवा",
      environment: "एनवायरनमेंट",
      llmProvider: "LLM प्रदाता",
      storage: "स्टोरेज",
      overall: "समग्र",
    },
    settings: {
      title: "सेटिंग्स",
      description:
        "स्थानीय, केवल-फ़्रंटएंड कॉन्फ़िगरेशन। यहाँ से कुछ भी कहीं नहीं भेजा जाता, सिवाय उस THYNACT API के जिससे आप जुड़ते हैं।",
      apiKeyPlaceholder: "अपनी THYNACT API कुंजी दर्ज करें",
      apiConnection: "API कनेक्शन",
      apiKeyNote:
        "API कुंजी sessionStorage में रखी जाती है — यह टैब बंद होते ही स्वतः हट जाती है और कभी डिस्क या लॉग में नहीं लिखी जाती। प्रोडक्शन में सर्वर-साइड ऑर्केस्ट्रेशन प्रॉक्सी को प्राथमिकता दें; यह फ़ॉर्म स्थानीय विकास और विश्वसनीय ऑपरेटर सत्रों के लिए है।",
      apiBaseUrl: "API बेस URL",
      apiKeyLabel: "API कुंजी (X-API-Key)",
      clear: "साफ़ करें",
    },
    notFound: {
      title: "पेज नहीं मिला",
      description: "यह स्क्रीन मौजूद नहीं है, या इसे हटा दिया गया है।",
    },
    workflows: {
      title: "वर्कफ़्लो",
      description:
        "एक स्टेप ग्राफ़ बनाएँ, फिर उसे चलाएँ। अलग से सहेजने की ज़रूरत नहीं — वर्कफ़्लो चलाने पर उसकी परिभाषा सुरक्षित हो जाती है।",
      viewRuns: "वर्कफ़्लो रन देखें",
      workflowName: "वर्कफ़्लो नाम",
      runContext: "रन संदर्भ (JSON)",
      stepGraph: "स्टेप ग्राफ़",
      addStep: "स्टेप जोड़ें",
      deleteSelected: "चयनित हटाएँ",
      runWorkflow: "वर्कफ़्लो चलाएँ",
      started: "वर्कफ़्लो आरंभ हुआ",
      runFailed: "रन विफल",
    },
    privacy: {
      title: "गोपनीयता और नीति",
      description: "THYNACT क्या संग्रहीत करता है, वह कहाँ जाता है, और सिस्टम स्वयं किन नियमों का पालन करता है।",
      lastUpdated: "अंतिम अद्यतन {date}",
    },
  },

  status: {
    LIVE_VALIDATED: "लाइव सत्यापित",
    CONNECTED_NOT_VALIDATED: "कनेक्टेड, सत्यापित नहीं",
    AUTH_REQUIRED: "प्रमाणीकरण आवश्यक",
    CREDENTIAL_REQUIRED: "क्रेडेंशियल आवश्यक",
    PROVIDER_APPROVAL_REQUIRED: "प्रदाता स्वीकृति आवश्यक",
    PLATFORM_CONFIG_REQUIRED: "प्लेटफ़ॉर्म कॉन्फ़िगरेशन आवश्यक",
    STABLE_DOMAIN_REQUIRED: "स्थिर डोमेन आवश्यक",
    DEGRADED: "सीमित",
    NOT_IMPLEMENTED: "लागू नहीं",
    UNAVAILABLE: "अनुपलब्ध",
    healthy: "स्वस्थ",
    running: "चल रहा है",
    succeeded: "सफल",
    failed: "विफल",
    pending: "लंबित",
    configured: "कॉन्फ़िगर किया गया",
  },

  /** StatusBadge display labels. The KEY is the machine status; only the
   * text is localized, so backend contracts are untouched. */
  badges: {
    pending: "लंबित",
    running: "चल रहा है",
    completed: "पूर्ण",
    succeeded: "सफल",
    failed: "विफल",
    rejected: "अस्वीकृत",
    paused: "रुका हुआ",
    skipped: "छोड़ा गया",
    waiting_approval: "स्वीकृति प्रतीक्षित",
    ok: "स्वस्थ",
    healthy: "स्वस्थ",
    unconfigured: "कॉन्फ़िगर नहीं",
    unavailable: "अनुपलब्ध",
    degraded: "सीमित",
    connected: "कनेक्टेड",
    configured: "कॉन्फ़िगर किया गया",
    needs_setup: "सेटअप आवश्यक",
    available: "उपलब्ध",
    error: "त्रुटि",
    disabled: "निष्क्रिय",
  },

  counts: {
    // Hindi does not inflect "कार्य" for number, but "घटना" does become
    // "घटनाएँ" — which is exactly why plural forms are per-locale rather than
    // an English rule applied everywhere.
    task_one: "{count} कार्य",
    task_other: "{count} कार्य",
    event_one: "{count} घटना",
    event_other: "{count} घटनाएँ",
    result_one: "{count} परिणाम",
    result_other: "{count} परिणाम",
  },
};
