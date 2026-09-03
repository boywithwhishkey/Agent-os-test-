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
    tasks: { title: "कार्य" },
    orchestrate: { title: "ऑर्केस्ट्रेट" },
    autonomous: { title: "स्वायत्त रन" },
    agents: { title: "एजेंट" },
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
    workflowRuns: { title: "वर्कफ़्लो रन" },
    approvals: { title: "स्वीकृतियाँ" },
    memory: { title: "मेमोरी" },
    runtime: { title: "रनटाइम" },
    tools: { title: "टूल" },
    integrations: { title: "इंटीग्रेशन" },
    audit: { title: "ऑडिट लॉग" },
    health: { title: "सिस्टम स्वास्थ्य" },
    settings: { title: "सेटिंग्स" },
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
