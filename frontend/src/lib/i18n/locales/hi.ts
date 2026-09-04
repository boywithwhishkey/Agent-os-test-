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
    operator: "ऑपरेटर",
    apiKeyConfigured: "API कुंजी कॉन्फ़िगर है",
    noApiKeySet: "कोई API कुंजी सेट नहीं",
    connections: "कनेक्शन",
    clearSession: "सत्र साफ़ करें",
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
    heroLead: "आपका कंट्रोल सेंटर",
    heroBody:
      "THYNACT को एक उद्देश्य दें और यह योजना बनाता है, सत्यापित करता है और निष्पादित करता है — हर परिणामकारी चरण नीति से होकर गुजरता है और ऑडिट ट्रेल में दर्ज होता है।",
    heroPrimary: "ऑर्केस्ट्रेशन शुरू करें",
    heroSecondary: "यह क्या करता है, देखें",
    exploreTitle: "एक्सप्लोर करें",
    explore: {
      overview: {
        title: "उत्पाद अवलोकन",
        body: "आज जो भी क्षमता लाइव है, हर एक उसी सतह से जुड़ी है जो उसे चलाती है।",
      },
      integrations: {
        title: "कनेक्टर",
        body: "कनेक्टर कैटलॉग ब्राउज़ करें और देखें कि क्या कनेक्टेड है, किसे सेटअप चाहिए, और क्या अभी बना नहीं है।",
      },
      about: {
        title: "THYNACT के बारे में",
        body: "यह क्यों है, इसमें काम कैसे आगे बढ़ता है, और यह किन बातों पर टिका है।",
      },
      health: {
        title: "सिस्टम स्वास्थ्य",
        body: "सीधे बैकएंड से लाइव स्थिति, स्टोरेज की टिकाऊपन सहित।",
      },
    },
    sessionEmptyHint: "इस टैब में आप जो भी शुरू करेंगे वह यहाँ दिखेगा।",
  },

  capabilities: {
    identity: {
      account: {
        read: "जुड़े हुए खाते को पढ़ना",
      },
    },
    mail: {
      message: {
        list: "संदेश सूचीबद्ध करना",
        read: "संदेश की सामग्री पढ़ना",
        send: "मेल भेजना",
      },
      draft: {
        create: "ड्राफ़्ट बनाना",
      },
    },
    calendar: {
      event: {
        list: "कैलेंडर इवेंट सूचीबद्ध करना",
        create: "कैलेंडर इवेंट बनाना",
        update: "कैलेंडर इवेंट बदलना",
        delete: "कैलेंडर इवेंट हटाना",
      },
    },
    files: {
      file: {
        list: "फ़ाइलें सूचीबद्ध करना",
        read: "फ़ाइल की सामग्री पढ़ना",
        write: "फ़ाइल बनाना या बदलना",
        delete: "फ़ाइल हटाना",
      },
    },
    chat: {
      message: {
        list: "चैनल के संदेश पढ़ना",
        send: "संदेश पोस्ट करना",
      },
    },
    docs: {
      page: {
        read: "पेज पढ़ना",
        write: "पेज बनाना या बदलना",
      },
    },
    tracker: {
      issue: {
        list: "इशू सूचीबद्ध करना",
        create: "इशू बनाना",
        update: "इशू अपडेट करना",
      },
    },
    repo: {
      metadata: {
        read: "रिपॉज़िटरी मेटाडेटा पढ़ना",
      },
      content: {
        read: "रिपॉज़िटरी की सामग्री पढ़ना",
      },
      issue: {
        create: "इशू या पुल रिक्वेस्ट खोलना",
      },
      branch: {
        merge: "ब्रांच मर्ज करना",
      },
    },
    automation: {
      run: {
        read: "निष्पादन का परिणाम पढ़ना",
      },
      workflow: {
        trigger: "बाहरी वर्कफ़्लो चलाना",
      },
    },
    ai: {
      model: {
        list: "उपलब्ध मॉडल सूचीबद्ध करना",
      },
      completion: {
        create: "मॉडल कम्प्लीशन चलाना",
      },
    },
    data: {
      record: {
        read: "रिकॉर्ड पढ़ना",
        write: "रिकॉर्ड लिखना",
      },
      search: {
        semantic: "सिमैंटिक खोज",
      },
    },
    queue: {
      job: {
        read: "कतार में लगे जॉब पढ़ना",
        enqueue: "जॉब कतार में डालना",
      },
    },
    crm: {
      contact: {
        list: "CRM संपर्क सूचीबद्ध करना",
        update: "CRM संपर्क अपडेट करना",
      },
      deal: {
        list: "डील सूचीबद्ध करना",
      },
      ticket: {
        list: "टिकट सूचीबद्ध करना",
      },
    },
    commerce: {
      payment: {
        list: "भुगतान सूचीबद्ध करना",
      },
      subscription: {
        list: "सब्सक्रिप्शन सूचीबद्ध करना",
      },
      refund: {
        create: "रिफ़ंड जारी करना",
      },
    },
    cloud: {
      service: {
        read: "सेवा की स्थिति पढ़ना",
      },
      dns: {
        read: "DNS और एज कॉन्फ़िगरेशन पढ़ना",
      },
      deploy: {
        trigger: "डिप्लॉयमेंट चलाना",
      },
    },
    auth: {
      user: {
        list: "प्रमाणित उपयोगकर्ता सूचीबद्ध करना",
      },
    },
  },

  pages: {
    overview: {
      title: "उत्पाद अवलोकन",
      heroTitle: "एक एजेंट प्लेटफ़ॉर्म जो पहले सोचता है, फिर आपके नियंत्रण में कार्य करता है।",
      heroBody:
        "THYNACT योजना बनाता है, कार्य सौंपता है, सत्यापित करता है और निष्पादित करता है — हर परिणामकारी कार्रवाई नीति द्वारा नियंत्रित, ऑडिट ट्रेल में दर्ज, और उस अनुरोध तक जाँची जा सकने योग्य जिसने उसे उत्पन्न किया।",
      whatItDoes: "यह क्या करता है",
      everyItemLinks: "हर आइटम लाइव सतह से जुड़ा है",
      howItStaysTrustworthy: "यह भरोसेमंद कैसे रहता है",
      trustworthyBody:
        "स्वायत्तता तभी उपयोगी है जब उसकी सीमाएँ हों। ये सीमाएँ कोड में लागू हैं, किसी नीति दस्तावेज़ में लिखी हुई नहीं।",
      startOrchestration: "ऑर्केस्ट्रेशन आरंभ करें",
      browseConnectors: "कनेक्टर देखें",
      connectors: "कनेक्टर",
      viewIntegrations: "इंटीग्रेशन देखें",
      pillars: {
        reason: {
          title: "कार्य से पहले विचार",
          body: "हर अनुरोध जटिलता, विश्वास और जोखिम के आधार पर रूट होता है। सरल अनुरोध तेज़, नियतात्मक पथ पर ही रहते हैं; केवल वही काम योजना या कई specialists की लागत उठाता है जिसे सचमुच उसकी ज़रूरत हो।",
          action: "ऑर्केस्ट्रेट",
        },
        threeRole: {
          title: "तीन-भूमिका ऑर्केस्ट्रेशन",
          body: "Researcher, builder और reviewer एक समन्वित योजना के रूप में, वास्तविक समानांतरता सीमा के साथ चलते हैं — जिससे जटिल उद्देश्य एक ही चरण में उत्तर पाने के बजाय विभाजित और जाँचे जाते हैं।",
          action: "स्वायत्त रन",
        },
        workflow: {
          title: "टिकाऊ वर्कफ़्लो इंजन",
          body: "निर्भरता सत्यापन, पुनःप्रयास, टाइमआउट, शर्तों और स्वीकृति द्वारों के साथ विज़ुअल DAG बिल्डर। रन सुरक्षित रहते हैं और ठहराव के बाद फिर से शुरू किए जा सकते हैं।",
          action: "वर्कफ़्लो बनाएँ",
        },
        tools: {
          title: "नियंत्रित टूल निष्पादन",
          body: "हर टूल का एक जोखिम स्तर होता है। पढ़ने वाले टूल स्वतंत्र रूप से चलते हैं; लिखने और उच्च-जोखिम वाले टूल के लिए एकल-उपयोग स्वीकृति चाहिए, जिसे मॉडल स्वयं जारी नहीं कर सकता।",
          action: "टूल रजिस्ट्री",
        },
        memory: {
          title: "सिमेंटिक + लेक्सिकल मेमोरी",
          body: "pgvector पर हाइब्रिड रिट्रीवल, वास्तविक प्रासंगिकता स्कोरिंग के साथ — सिमेंटिक समानता, लेक्सिकल मिलान और महत्व भार; नाम बदलकर परोसी गई कीवर्ड खोज नहीं।",
          action: "मेमोरी खोजें",
        },
        runtime: {
          title: "दिखाई देने वाला रनटाइम",
          body: "सर्किट ब्रेकर, स्लाइडिंग-विंडो रेट लिमिट, सीमित पुनःप्रयास और idempotency कुंजियाँ — हर एक की लाइव स्थिति लॉग से अनुमान लगाने के बजाय सीधे देखी जा सकती है।",
          action: "रनटाइम स्थिति",
        },
      },
      governance: {
        authority: {
          title: "मॉडल की बुद्धिमत्ता अधिकार नहीं है",
          body: "क्षमता का अर्थ अनुमति कभी नहीं। भेजना, प्रकाशित करना, हटाना, खरीदना, रिफ़ंड, खर्च, डिप्लॉय और एडमिन परिवर्तन नीति से होकर गुज़रते हैं और, जहाँ आवश्यक हो, स्पष्ट स्वीकृति से।",
        },
        audited: {
          title: "हर निष्पादन ऑडिट होता है",
          body: "टूल रन में टूल, जोखिम, परिणाम, स्वीकृति आवश्यकता और उस अनुरोध की कोरिलेशन ID दर्ज होती है जिसने उसे उत्पन्न किया — ताकि हर कार्रवाई अपने स्रोत तक जाँची जा सके।",
        },
        untrusted: {
          title: "अविश्वसनीय सामग्री केवल डेटा है",
          body: "ईमेल, वेब पेज, दस्तावेज़, कनेक्टर या MCP टूल से लौटा पाठ डेटा माना जाता है, निर्देश कभी नहीं। अज्ञात MCP टूल डिफ़ॉल्ट रूप से अस्वीकृत है।",
        },
        honest: {
          title: "ईमानदार क्षमता स्थितियाँ",
          body: "कोई कनेक्टर इसलिए \"काम कर रहा\" नहीं माना जाता कि उसका एडाप्टर या कार्ड मौजूद है। हर एक अपनी वास्तविक स्थिति बताता है — लाइव-सत्यापित, क्रेडेंशियल-आवश्यक या लागू-नहीं — और कुछ भी बढ़ा-चढ़ाकर नहीं दिखाया जाता।",
        },
      },
      connectorsBody:
        "प्रदाताओं तक एक ब्रोकर के माध्यम से पहुँचा जाता है जो पहले आधिकारिक MCP, फिर सत्यापित MCP, फिर प्रबंधित कनेक्टर, फिर नेटिव एडाप्टर को प्राथमिकता देता है। इंटीग्रेशन पेज हर एक की वास्तविक स्थिति दिखाता है — कनेक्टेड, क्रेडेंशियल आवश्यक, या लागू नहीं — न कि ऐसी गिनती जो उत्पाद को बढ़ा-चढ़ाकर दिखाए।",
      mcpFirst: "MCP-पहले, केवल-MCP नहीं",
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
        "इंटीग्रेशन को जोड़ने, कॉन्फ़िगर करने या टेस्ट करने के लिए ऑपरेटर एक्सेस चाहिए — नीचे का कैटलॉग फिर भी देखा जा सकता है।",
      actions: {
        test: "टेस्ट",
        testConnection: "कनेक्शन टेस्ट करें",
        testFailed: "कनेक्शन टेस्ट विफल रहा",
        manage: "प्रबंधित करें",
        learnMore: "और जानें",
        connect: "{name} से जुड़ें",
        configure: "कॉन्फ़िगर करें",
        configureWebhook: "वेबहुक कॉन्फ़िगर करें",
        disconnect: "डिस्कनेक्ट करें",
        execute: "चलाएँ",
      },
      detail: {
        catalogOnly:
          "केवल कैटलॉग — यह कनेक्टर अभी बना नहीं है। यह बताता है कि THYNACT किसे सहारा दे सकता है; जब तक इसे लागू नहीं किया जाता, न कोई क्रेडेंशियल लिया जाता है और न ही कोई कनेक्शन संभव है।",
        requiresSetupPrefix: "सेटअप आवश्यक। इस कनेक्टर को जुड़ने से पहले बैकएंड पर",
        requiresSetupSuffix: "कॉन्फ़िगर होना चाहिए।",
        authorityTitle: "इसे जोड़ने से क्या अधिकार मिलता है",
        authorityBody:
          "घोषित क्षमताएँ। ये बताती हैं कि एक कनेक्शन कितना अधिकार रखेगा — यह नहीं कि हर एक अभी लागू हो चुकी है।",
        canRead: "पढ़ सकता है",
        canChange: "बदल सकता है",
        needsApproval: "आपकी स्वीकृति चाहिए",
        needsApprovalBody: "THYNACT इन्हें तैयार कर सकता है, पर स्वयं पूरा नहीं कर सकता।",
        mcpUnmapped:
          "इस MCP सर्वर से मिले टूल कैनोनिकल क्षमताओं से मैप नहीं हैं। जब तक मैप न हो, अज्ञात टूल अस्वीकृत रहता है — कोई सर्वर अपना जोखिम स्तर स्वयं तय नहीं कर सकता।",
        systemInfrastructure: "सिस्टम इंफ्रास्ट्रक्चर",
        systemInfrastructureBody:
          "यह THYNACT के अपने चालू सिस्टम का हिस्सा है, कोई खाता नहीं जिसे आप जोड़ते हैं। निदान के लिए दिखाया गया है।",
        authType: "प्रमाणीकरण प्रकार",
        lastCheck: "अंतिम जाँच",
        latency: "विलंब",
        lastError: "अंतिम त्रुटि",
        lastExecution: "अंतिम निष्पादन",
        never: "कभी नहीं",
        docs: "दस्तावेज़",
        capabilities: "क्षमताएँ",
        plannedCapabilities: "नियोजित क्षमताएँ",
        tools: "टूल",
        resources: "रिसोर्स",
        prompts: "प्रॉम्प्ट",
        noCapabilitiesYet: "अभी तक कोई क्षमता नहीं मिली — ताज़ा करने के लिए कनेक्शन टेस्ट चलाएँ।",
        executeWorkflow: "एक वर्कफ़्लो चलाएँ",
        webhookWorkflow: "वेबहुक वर्कफ़्लो",
        payloadJson: "पेलोड (JSON)",
        payloadInvalid: "पेलोड मान्य JSON होना चाहिए",
        success: "सफल",
        failed: "विफल",
        disconnectNamed: "{name} को डिस्कनेक्ट करें?",
        disconnectMcp: "इस MCP सर्वर को डिस्कनेक्ट करें?",
        disconnectOAuthBody: "यह सहेजा गया खाता कनेक्शन भुला देता है। आप कभी भी दोबारा अधिकृत कर सकते हैं।",
        disconnectMcpBody: "यह सर्वर कॉन्फ़िगरेशन हटा देता है। इसे पूर्ववत नहीं किया जा सकता।",
      },
      browseTitle: "कनेक्टर ब्राउज़ करें",
      browseBody:
        "यहाँ हर प्रविष्टि उसकी लाइव स्थिति के साथ एक वास्तविक कैटलॉग रिकॉर्ड है। प्रोटोकॉल नाम (MCP, API, OAuth, webhook) खोजे जा सकते हैं।",
      allStatuses: "सभी",
      allCategories: "सभी श्रेणियाँ",
      showingCount: "{total} में से {shown} कनेक्टर दिखाए जा रहे हैं",
      buckets: {
        connected: {
          label: "कनेक्टेड",
          hint: "वास्तविक प्रदाता के विरुद्ध सत्यापित।",
        },
        needs_verification: {
          label: "सत्यापन आवश्यक",
          hint: "क्रेडेंशियल सेट हैं पर यह सिद्ध नहीं हुआ कि वे काम करते हैं। एक टेस्ट चलाएँ।",
        },
        needs_setup: {
          label: "सेटअप आवश्यक",
          hint: "बना हुआ और तैयार — क्रेडेंशियल या अधिकृतीकरण की प्रतीक्षा में।",
        },
        not_built: {
          label: "अभी नहीं बना",
          hint: "केवल कैटलॉग मेटाडेटा। इनके पीछे कोई अडैप्टर नहीं है।",
        },
      },
      categories: {
        ai: "AI",
        automation: "ऑटोमेशन",
        productivity: "उत्पादकता",
        google: "Google",
        developer: "डेवलपर",
        data: "डेटा",
        other: "अन्य",
      },
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
    about: {
      title: "THYNACT के बारे में",
      navLabel: "THYNACT के बारे में",
      heroStatement:
        "बुद्धिमत्ता को केवल उत्तर देने से आगे जाना चाहिए। उसे काम को सुरक्षित रूप से आगे बढ़ाना चाहिए।",
      whyTitle: "THYNACT क्यों है",
      whyBody:
        "अधिकांश AI उत्तर पर रुक जाता है। एक अच्छे उत्तर और पूरे हुए काम के बीच की दूरी में ही असली सिस्टम रहते हैं — क्रेडेंशियल, अनुमतियाँ, दुष्प्रभाव, और यह प्रश्न कि किसने क्या अधिकृत किया। THYNACT इस दूरी को पाटने के लिए बना है, यह दिखावा किए बिना कि यह दूरी कभी थी ही नहीं।",
      thinkTitle: "सोचना",
      thinkBody:
        "अनुरोध को समझना, जटिलता और जोखिम के अनुसार रूट करना, जो ज़रूरी है उसे याद रखना, योजना तभी बनाना जब वह अपनी लागत वसूल करे, और कार्य से पहले सत्यापित करना।",
      actTitle: "कार्य",
      actBody:
        "एक नियंत्रित ब्रोकर के माध्यम से वास्तविक सेवाओं तक पहुँचना, निष्पादित करना, स्वचालित करना और शेड्यूल करना — और हर चरण दर्ज करना ताकि परिणाम उस अनुरोध तक जाँचा जा सके जिसने उसे उत्पन्न किया।",
      controlTitle: "नियंत्रण",
      controlBody:
        "हर परिणामकारी कार्रवाई के चारों ओर अनुमति, स्वीकृति, पहचान और टेनेंट सीमाएँ रहती हैं। क्षमता चुपचाप अधिकार नहीं बन जाती।",
      flowTitle: "THYNACT में काम कैसे आगे बढ़ता है",
      flowBody:
        "परिणामकारी चरण नियंत्रण से होकर गुज़रते हैं। बाकी सब तेज़ पथ लेता है।",
      flow: {
        intent: "इरादा",
        think: "सोचना",
        plan: "योजना",
        verify: "सत्यापन",
        act: "कार्य",
        result: "परिणाम",
        control: "नियंत्रण",
      },
      principlesTitle: "यह किन बातों पर टिका है",
      principles: {
        fast: {
          title: "डिफ़ॉल्ट रूप से तेज़",
          body: "सरल काम सरल ही रहता है। योजना, रिट्रीवल और मल्टी-एजेंट निष्पादन वैकल्पिक लागत हैं, डिफ़ॉल्ट पथ कभी नहीं।",
        },
        real: {
          title: "नकल नहीं, वास्तविकता",
          body: "\"काम कर रहा है\" का अर्थ है वास्तविक प्रदाता के साथ वास्तविक निष्पादन से सत्यापित — न कि यह कि कोई एडाप्टर, कार्ड या पास होता मॉक मौजूद है।",
        },
        authority: {
          title: "बुद्धिमत्ता अधिकार नहीं है",
          body: "भेजना, प्रकाशित करना, हटाना, खर्च करना और डिप्लॉय करना नीति से होकर गुज़रते हैं और, जहाँ आवश्यक हो, ऐसी स्वीकृति से जो मॉडल स्वयं को नहीं दे सकता।",
        },
        neutral: {
          title: "प्रदाता-निरपेक्ष",
          body: "मॉडल और टूल बदले जा सकने वाला इंफ़्रास्ट्रक्चर हैं। मूल तर्क कैनोनिकल क्षमताओं की भाषा बोलता है, किसी वेंडर के API नामों की नहीं।",
        },
        continuity: {
          title: "निरंतरता के लिए बना",
          body: "मेमोरी, वर्कफ़्लो और टिकाऊ स्थिति सत्र से आगे टिकने के लिए बनाई गई हैं, ताकि काम फिर से शुरू करने के बजाय आगे बढ़ाया जा सके।",
        },
        governed: {
          title: "नियंत्रित कार्रवाई",
          body: "हर टूल रन उसके परिणाम और उसके पीछे के अनुरोध की कोरिलेशन ID के साथ दर्ज होता है। ऐसा ऑडिट ट्रेल जिसे चुपचाप बदला जा सके, ऑडिट ट्रेल नहीं है।",
        },
      },
      visionTitle: "यह किस दिशा में जा रहा है",
      visionBody:
        "यह दिशा है, उपलब्ध क्षमता नहीं। आज क्या लाइव है, यह उत्पाद अवलोकन और सिस्टम स्वास्थ्य पेज पर दिखता है।",
      vision: {
        surfaces: "और सतहें — वेब कंट्रोल सेंटर के साथ मोबाइल और वॉइस",
        connectors: "व्यावसायिक सिस्टम में व्यापक कनेक्टर कवरेज",
        automation: "समृद्ध शेड्यूल्ड और इवेंट-आधारित ऑटोमेशन",
        multimodal: "मल्टीमॉडल समझ, जहाँ वह काम में सचमुच मदद करे",
      },
      ctaTitle: "जब आप तैयार हों",
      ctaBody: "कोई सेवा कनेक्ट करें, या THYNACT को एक उद्देश्य दें और उसे काम करते देखें।",
      ctaPrimary: "डैशबोर्ड खोलें",
      ctaSecondary: "कनेक्टर देखें",
      shipped: "आज उपलब्ध",
      direction: "दिशा",
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
