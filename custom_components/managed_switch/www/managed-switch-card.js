var N=globalThis,U=N.ShadowRoot&&(N.ShadyCSS===void 0||N.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,z=Symbol(),lt=new WeakMap,k=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==z)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(U&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=lt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&lt.set(e,t))}return t}toString(){return this.cssText}},ct=n=>new k(typeof n=="string"?n:n+"",void 0,z),I=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((s,i,r)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[r+1],n[0]);return new k(e,n,z)},dt=(n,t)=>{if(U)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=N.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,n.appendChild(s)}},W=U?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return ct(e)})(n):n;var{is:Nt,defineProperty:Ut,getOwnPropertyDescriptor:Mt,getOwnPropertyNames:Ot,getOwnPropertySymbols:Ht,getPrototypeOf:jt}=Object,M=globalThis,ht=M.trustedTypes,Dt=ht?ht.emptyScript:"",zt=M.reactiveElementPolyfillSupport,E=(n,t)=>n,F={toAttribute(n,t){switch(t){case Boolean:n=n?Dt:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},ut=(n,t)=>!Nt(n,t),pt={attribute:!0,type:String,converter:F,reflect:!1,useDefault:!1,hasChanged:ut};Symbol.metadata??=Symbol("metadata"),M.litPropertyMetadata??=new WeakMap;var m=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=pt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Ut(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:r}=Mt(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let l=i?.call(this);r?.call(this,o),this.requestUpdate(t,l,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??pt}static _$Ei(){if(this.hasOwnProperty(E("elementProperties")))return;let t=jt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(E("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(E("properties"))){let e=this.properties,s=[...Ot(e),...Ht(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(W(i))}else t!==void 0&&e.push(W(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return dt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let r=(s.converter?.toAttribute!==void 0?s.converter:F).toAttribute(e,s.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=s.getPropertyOptions(i),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:F;this._$Em=i;let l=o.fromAttribute(e,r.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(t!==void 0){let o=this.constructor;if(i===!1&&(r=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??ut)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,r]of s){let{wrapped:o}=r,l=this[i];o!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,r,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};m.elementStyles=[],m.shadowRootOptions={mode:"open"},m[E("elementProperties")]=new Map,m[E("finalized")]=new Map,zt?.({ReactiveElement:m}),(M.reactiveElementVersions??=[]).push("2.1.2");var J=globalThis,ft=n=>n,O=J.trustedTypes,gt=O?O.createPolicy("lit-html",{createHTML:n=>n}):void 0,bt="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,yt="?"+$,It=`<${yt}>`,y=document,P=()=>y.createComment(""),R=n=>n===null||typeof n!="object"&&typeof n!="function",Z=Array.isArray,Wt=n=>Z(n)||typeof n?.[Symbol.iterator]=="function",B=`[ 	
\f\r]`,C=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,mt=/-->/g,_t=/>/g,w=RegExp(`>|${B}(?:([^\\s"'>=/]+)(${B}*=${B}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),$t=/'/g,vt=/"/g,xt=/^(?:script|style|textarea|title)$/i,Q=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),f=Q(1),Zt=Q(2),Qt=Q(3),x=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),wt=new WeakMap,b=y.createTreeWalker(y,129);function St(n,t){if(!Z(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return gt!==void 0?gt.createHTML(t):t}var Ft=(n,t)=>{let e=n.length-1,s=[],i,r=t===2?"<svg>":t===3?"<math>":"",o=C;for(let l=0;l<e;l++){let a=n[l],d,h,c=-1,u=0;for(;u<a.length&&(o.lastIndex=u,h=o.exec(a),h!==null);)u=o.lastIndex,o===C?h[1]==="!--"?o=mt:h[1]!==void 0?o=_t:h[2]!==void 0?(xt.test(h[2])&&(i=RegExp("</"+h[2],"g")),o=w):h[3]!==void 0&&(o=w):o===w?h[0]===">"?(o=i??C,c=-1):h[1]===void 0?c=-2:(c=o.lastIndex-h[2].length,d=h[1],o=h[3]===void 0?w:h[3]==='"'?vt:$t):o===vt||o===$t?o=w:o===mt||o===_t?o=C:(o=w,i=void 0);let g=o===w&&n[l+1].startsWith("/>")?" ":"";r+=o===C?a+It:c>=0?(s.push(d),a.slice(0,c)+bt+a.slice(c)+$+g):a+$+(c===-2?l:g)}return[St(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},L=class n{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,o=0,l=t.length-1,a=this.parts,[d,h]=Ft(t,e);if(this.el=n.createElement(d,s),b.currentNode=this.el.content,e===2||e===3){let c=this.el.content.firstChild;c.replaceWith(...c.childNodes)}for(;(i=b.nextNode())!==null&&a.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let c of i.getAttributeNames())if(c.endsWith(bt)){let u=h[o++],g=i.getAttribute(c).split($),v=/([.?@])?(.*)/.exec(u);a.push({type:1,index:r,name:v[2],strings:g,ctor:v[1]==="."?q:v[1]==="?"?K:v[1]==="@"?G:A}),i.removeAttribute(c)}else c.startsWith($)&&(a.push({type:6,index:r}),i.removeAttribute(c));if(xt.test(i.tagName)){let c=i.textContent.split($),u=c.length-1;if(u>0){i.textContent=O?O.emptyScript:"";for(let g=0;g<u;g++)i.append(c[g],P()),b.nextNode(),a.push({type:2,index:++r});i.append(c[u],P())}}}else if(i.nodeType===8)if(i.data===yt)a.push({type:2,index:r});else{let c=-1;for(;(c=i.data.indexOf($,c+1))!==-1;)a.push({type:7,index:r}),c+=$.length-1}r++}}static createElement(t,e){let s=y.createElement("template");return s.innerHTML=t,s}};function S(n,t,e=n,s){if(t===x)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,r=R(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(n),i._$AT(n,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=S(n,i._$AS(n,t.values),i,s)),t}var V=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??y).importNode(e,!0);b.currentNode=i;let r=b.nextNode(),o=0,l=0,a=s[0];for(;a!==void 0;){if(o===a.index){let d;a.type===2?d=new T(r,r.nextSibling,this,t):a.type===1?d=new a.ctor(r,a.name,a.strings,this,t):a.type===6&&(d=new Y(r,this,t)),this._$AV.push(d),a=s[++l]}o!==a?.index&&(r=b.nextNode(),o++)}return b.currentNode=y,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},T=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=S(this,t,e),R(t)?t===p||t==null||t===""?(this._$AH!==p&&this._$AR(),this._$AH=p):t!==this._$AH&&t!==x&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Wt(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==p&&R(this._$AH)?this._$AA.nextSibling.data=t:this.T(y.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=L.createElement(St(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new V(i,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=wt.get(t.strings);return e===void 0&&wt.set(t.strings,e=new L(t)),e}k(t){Z(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let r of t)i===e.length?e.push(s=new n(this.O(P()),this.O(P()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=ft(t).nextSibling;ft(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},A=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=p,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=p}_$AI(t,e=this,s,i){let r=this.strings,o=!1;if(r===void 0)t=S(this,t,e,0),o=!R(t)||t!==this._$AH&&t!==x,o&&(this._$AH=t);else{let l=t,a,d;for(t=r[0],a=0;a<r.length-1;a++)d=S(this,l[s+a],e,a),d===x&&(d=this._$AH[a]),o||=!R(d)||d!==this._$AH[a],d===p?t=p:t!==p&&(t+=(d??"")+r[a+1]),this._$AH[a]=d}o&&!i&&this.j(t)}j(t){t===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},q=class extends A{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===p?void 0:t}},K=class extends A{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==p)}},G=class extends A{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=S(this,t,e,0)??p)===x)return;let s=this._$AH,i=t===p&&s!==p||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==p&&(s===p||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},Y=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t)}};var Bt=J.litHtmlPolyfillSupport;Bt?.(L,T),(J.litHtmlVersions??=[]).push("3.3.3");var At=(n,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let r=e?.renderBefore??null;s._$litPart$=i=new T(t.insertBefore(P(),r),r,void 0,e??{})}return i._$AI(n),i};var X=globalThis,_=class extends m{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=At(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return x}};_._$litElement$=!0,_.finalized=!0,X.litElementHydrateSupport?.({LitElement:_});var Vt=X.litElementPolyfillSupport;Vt?.({LitElement:_});(X.litElementVersions??=[]).push("4.2.2");function tt(n,t){let{code:e,message:s}=n??{};return e==="unknown_command"?t.oldIntegration:e==="not_found"?t.notFound:s??String(n)}var H=class{constructor(t){this.changed=t;this.loadedAt=0;this.pending=!1}reset(){this.reply=void 0,this.error=void 0,this.deviceId=void 0,this.loadedAt=0}load(t,e,s,i=!1){if(this.pending&&this.deviceId===e)return;let r=this.error===void 0?3e5:15e3;this.deviceId===e&&!i&&s-this.loadedAt<r||(this.deviceId!==e&&(this.reply=void 0),this.deviceId=e,this.loadedAt=s,this.pending=!0,t({type:"managed_switch/ports",device_id:e}).then(o=>this.settle(e,o,void 0),o=>this.settle(e,void 0,o??"error")))}settle(t,e,s){t===this.deviceId&&(this.pending=!1,e&&(this.reply=e),this.error=s,this.changed())}};var qt={"1.3.6.1.4.1.11.2.3.7.11.186":{rows:[["1","2","3","4","5","6","7","8"]],sfp:[]},"1.3.6.1.4.1.11.2.3.7.11.194":{rows:[["1","2","3","4","5","6","7","8"]],sfp:["9","10"]}},et=12;function st(n,t){let e=new Set(n.ports.filter(o=>o.kind==="ethernet").map(o=>o.name)),s=t??qt[n.switch.object_id??""];if(s){let o=s.rows.map(h=>h.filter(c=>e.has(c))).filter(h=>h.length),l=s.sfp.filter(h=>e.has(h)),a=new Set([...o.flat(),...l]),d=[...e].filter(h=>!a.has(h));return{rows:d.length?[...o,d]:o,sfp:l}}let i=n.ports.filter(o=>o.kind==="ethernet").map(o=>o.name);if(i.length<=et)return{rows:i.length?[i]:[],sfp:[]};let r=[];for(let o=0;o<i.length;o+=et*2){let l=i.slice(o,o+et*2);r.push(l.filter((a,d)=>d%2===0),l.filter((a,d)=>d%2===1))}return{rows:r.filter(o=>o.length),sfp:[]}}function it(n,t){if(!n||n.state==="unavailable"||n.state==="unknown")return"unknown";if(n.state!=="on")return"down";let e=t?.state?Number(t.state):NaN;return Number.isFinite(e)?e>=1e3?"fast":e>=100?"slow":"slowest":"up"}function Et(n){let t=n?.state?Number(n.state):NaN;return!Number.isFinite(t)||t<=0?"":t>=1e3?`${t/1e3}G`:`${t}`}function nt(n){let t=n?.state?Number(n.state):NaN;return Number.isFinite(t)?t:void 0}function Ct(n){return n?.state==="delivering_power"}function Pt(n,t=18){let e=n&&!["unknown","unavailable",""].includes(n.state)?n.state:"";return e.length>t?`${e.slice(0,t-1)}\u2026`:e}function ot(n){let t=Number(n?.state);if(!n||!Number.isFinite(t))return"";let e=String(n.attributes.unit_of_measurement??""),s=e==="bit/s"?t/1e6:e==="kbit/s"?t/1e3:t;return s>=100?`${Math.round(s)}`:s.toFixed(s>=10?0:1)}function Rt(n,t,e,s=i=>i.state){let i=[`${e.port} ${n.name}${n.alias?` \xB7 ${n.alias}`:""}`],r=t[n.entities.link??""],o=t[n.entities.speed??""],l=it(r,o),a={down:e.noLink,unknown:e.unknown,up:e.linkUp};if(i.push(l in a?a[l]:`${o?.state} Mbit/s`),n.uplink&&i.push(e.uplink),n.poe){let c=t[n.entities.poe??""];i.push(`PoE: ${c?s(c):"?"}`)}let h=t[n.entities.device??""]?.attributes.devices??[];for(let c of h.slice(0,10))i.push(`\u2022 ${c.name??c.mac??"?"}`);return h.length>10&&i.push(`\u2026 +${h.length-10}`),i.join(`
`)}var kt={en:{port:"Port",noLink:"No link",linkUp:"Link",unknown:"Unknown",uplink:"Link to another switch",trunks:"Trunks",noSwitch:"Choose a managed switch in the card's settings.",oldIntegration:"This card needs the Managed Switch (SNMP) integration 0.2.0 or newer.",notFound:"The switch is not set up (yet), or the card's device is not a managed switch.",fields:{device_id:"Switch",title:"Title (optional)",show_names:"Device names under the ports",show_speed:"Speed in the ports",show_rates:"Data rates (sensors must be on)"}},de:{port:"Port",noLink:"Kein Link",linkUp:"Link",unknown:"Unbekannt",uplink:"Verbindung zu einem anderen Switch",trunks:"Trunks",noSwitch:"W\xE4hle in den Einstellungen der Karte einen Managed Switch.",oldIntegration:"Diese Karte braucht die Integration Managed Switch (SNMP) 0.2.0 oder neuer.",notFound:"Der Switch ist (noch) nicht eingerichtet, oder das Ger\xE4t der Karte ist kein Managed Switch.",fields:{device_id:"Switch",title:"Titel (optional)",show_names:"Ger\xE4tenamen unter den Ports",show_speed:"Geschwindigkeit in den Ports",show_rates:"Datenraten (Sensoren m\xFCssen an sein)"}}};function j(n){return kt[(n??"en").split("-")[0]]??kt.en}function Lt(n,t){return n?n.ports.map(e=>t[e.entities.link??""]?.state==="unavailable"?"0":"1").join(""):""}function Tt(n,t){return 1+2*Math.max(n?.rows.length??1,n?.sfp.length?1:0,1)+(t?2:0)}var rt=class extends _{constructor(){super(...arguments);this._loader=new H(()=>this.requestUpdate());this._available="";this._format=e=>this.hass?.formatEntityState?.(e)??e.state}static{this.properties={hass:{attribute:!1},_config:{state:!0}}}static getConfigElement(){return document.createElement("managed-switch-card-editor")}static getStubConfig(e){return{device_id:Object.values(e.entities??{}).find(i=>i?.platform==="managed_switch"&&i.device_id)?.device_id??void 0,show_names:!0,show_speed:!0,show_rates:!1}}setConfig(e){this._config={show_names:!0,show_speed:!0,show_rates:!1,...e},this._loader.reset(),this._available=""}getCardSize(){let e=this._loader.reply;if(!e)return 3;let s=e.ports.filter(i=>i.kind==="trunk").length;return Tt(st(e,this._config?.layout),s)}getGridOptions(){return{columns:12,min_columns:6,rows:"auto"}}updated(e){super.updated(e);let s=this._config?.device_id;if(!this.hass||!s)return;let i=this.hass,r=Lt(this._loader.reply,i.states),o=this._available!==""&&r!==this._available&&!r.includes("0");this._available=r,this._loader.load(l=>i.callWS(l),s,Date.now(),o)}_open(e){e&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}_port(e,s=!1){let i=this.hass?.states??{},r=j(this.hass?.language),o=e.entities,l=it(i[o.link??""],i[o.speed??""]),a=this._config?.show_rates?[ot(i[o.received??""]),ot(i[o.sent??""])]:["",""],d=Rt(e,i,r,this._format);return f`
      <button
        class="port ${l} ${s?"sfp":""}"
        title=${d}
        aria-label=${d.replaceAll(`
`,", ")}
        @click=${()=>this._open(o.device??o.link)}
      >
        <span class="jack">
          ${e.uplink?f`<ha-icon icon="mdi:swap-horizontal-bold" class="badge link"></ha-icon>`:p}
          ${e.poe&&Ct(i[o.poe??""])?f`<ha-icon icon="mdi:flash" class="badge poe"></ha-icon>`:p}
          <span class="bottom">
            ${e.trunk!==null?f`<span class="trunk">T</span>`:p}
            ${this._config?.show_speed&&["fast","slow","slowest"].includes(l)?f`<span class="speed">${Et(i[o.speed??""])}</span>`:p}
          </span>
        </span>
        <span class="name">${e.name}</span>
        ${this._config?.show_names?f`<span class="device">${Pt(i[o.device??""])}</span>`:p}
        ${a[0]||a[1]?f`<span class="rate">↓${a[0]||"\u2013"} ↑${a[1]||"\u2013"}</span>`:p}
      </button>
    `}render(){let e=j(this.hass?.language);if(!this._config?.device_id)return f`<ha-card><div class="note">${e.noSwitch}</div></ha-card>`;let s=this._loader.reply,i=this._loader.error;if(!s){let u=i===void 0?"\u2026":tt(i,e);return f`<ha-card><div class="note">${u}</div></ha-card>`}let r=new Map(s.ports.map(u=>[u.name,u])),o=st(s,this._config.layout),l=s.ports.filter(u=>u.kind==="trunk"),a=this.hass?.states??{},d=s.switch.entities,h=nt(a[d.poe_consumption??""]),c=nt(a[d.poe_budget??""]);return f`
      <ha-card>
        <div class="header">
          <div>
            <div class="title">${this._config.title??s.switch.name}</div>
            <div class="model">${[s.switch.model,s.switch.firmware].filter(Boolean).join(" \xB7 ")}</div>
          </div>
          ${h!==void 0&&c!==void 0?f`<button class="poe-total" @click=${()=>this._open(d.poe_consumption)}>
                <ha-icon icon="mdi:flash"></ha-icon>${h} / ${c} W
              </button>`:p}
        </div>
        ${i!==void 0?f`<div class="note">${tt(i,e)}</div>`:p}
        <div class="panel">
          <div class="rows">
            ${o.rows.map(u=>f`<div class="row">
                ${u.map(g=>{let v=r.get(g);return v?this._port(v):p})}
              </div>`)}
          </div>
          ${o.sfp.length?f`<div class="row sfp-row">
                ${o.sfp.map(u=>{let g=r.get(u);return g?this._port(g,!0):p})}
              </div>`:p}
        </div>
        ${l.length?f`<div class="trunks">
              <span class="label">${e.trunks}</span>
              ${l.map(u=>this._port(u))}
            </div>`:p}
      </ha-card>
    `}static{this.styles=I`
    ha-card {
      padding: 12px 16px 16px;
    }
    .note {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
      margin-bottom: 12px;
    }
    .title {
      font-size: 1.2em;
      font-weight: 500;
    }
    .model {
      color: var(--secondary-text-color);
      font-size: 0.85em;
    }
    .poe-total {
      all: unset;
      display: flex;
      align-items: center;
      gap: 4px;
      cursor: pointer;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }
    .poe-total:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .poe-total ha-icon {
      --mdc-icon-size: 18px;
      color: var(--warning-color, #e5c07b);
    }
    .panel {
      display: flex;
      gap: 12px;
      padding: 10px;
      border-radius: 10px;
      background: var(--secondary-background-color);
      overflow-x: auto;
      /* the SFP ports move below the others when the card is too narrow for both */
      flex-wrap: wrap;
    }
    .rows {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1 1 0;
      min-width: min-content;
    }
    .row {
      display: flex;
      gap: 4px;
    }
    .sfp-row {
      flex: 0 0 auto;
      padding-left: 12px;
      border-left: 2px solid var(--divider-color);
      align-self: flex-start;
    }
    .port {
      all: unset;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      /* as wide as the card allows: 64 px each at most, 28 px at least */
      flex: 1 1 0;
      min-width: 28px;
      max-width: 64px;
      gap: 2px;
      font-size: 0.75em;
    }
    .sfp {
      flex: 0 0 auto;
      width: 52px;
    }
    .trunks .port {
      flex: 0 0 auto;
      width: 64px;
    }
    .port:focus-visible .jack {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .jack {
      position: relative;
      width: 100%;
      max-width: 40px;
      height: 32px;
      border-radius: 4px 4px 8px 8px;
      border: 2px solid var(--divider-color);
      box-sizing: border-box;
    }
    .sfp .jack {
      width: 46px;
      height: 22px;
      border-radius: 3px;
    }
    .fast .jack {
      background: var(--success-color, #43a047);
      border-color: var(--success-color, #43a047);
    }
    .slow .jack {
      background: var(--warning-color, #ffa600);
      border-color: var(--warning-color, #ffa600);
    }
    .slowest .jack {
      background: var(--error-color, #db4437);
      border-color: var(--error-color, #db4437);
    }
    .up .jack {
      background: var(--info-color, #039be5);
      border-color: var(--info-color, #039be5);
    }
    .down .jack {
      background: var(--card-background-color);
    }
    .unknown .jack {
      background: var(--disabled-color, #bdbdbd);
      opacity: 0.5;
    }
    /* trunk mark and speed in the lower half, under the link and PoE symbols */
    .bottom {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 1px;
      display: flex;
      justify-content: center;
      gap: 3px;
      font-size: 0.75em;
      font-weight: 600;
      line-height: 1.2;
      color: var(--text-primary-color, #fff);
      pointer-events: none;
    }
    .badge {
      position: absolute;
      --mdc-icon-size: 14px;
      color: var(--text-primary-color, #fff);
    }
    .badge.link {
      left: 2px;
      top: 2px;
    }
    .badge.poe {
      right: 2px;
      top: 2px;
    }
    .name {
      font-weight: 500;
      /* as wide as the port, however long the text: it does not widen the port */
      width: 0;
      min-width: 100%;
      text-align: center;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .device,
    .rate {
      color: var(--secondary-text-color);
      text-align: center;
      width: 0;
      min-width: 100%;
      font-size: 0.9em;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .trunks {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }
    .trunks .label {
      color: var(--secondary-text-color);
      margin-right: 4px;
    }
  `}},at=class extends _{constructor(){super(...arguments);this._label=e=>j(this.hass?.language).fields[e.name]??e.name}static{this.properties={hass:{attribute:!1},_config:{state:!0}}}setConfig(e){this._config=e}_schema(){return[{name:"device_id",required:!0,selector:{device:{integration:"managed_switch"}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_names",selector:{boolean:{}}},{name:"show_speed",selector:{boolean:{}}},{name:"show_rates",selector:{boolean:{}}}]}]}_changed(e){this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e.detail.value},bubbles:!0,composed:!0}))}render(){return!this.hass||!this._config?f``:f`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema()}
      .computeLabel=${this._label}
      @value-changed=${this._changed}
    ></ha-form>`}};customElements.get("managed-switch-card")||(customElements.define("managed-switch-card",rt),customElements.define("managed-switch-card-editor",at));var D=window;D.customCards=D.customCards??[];D.customCards.some(n=>n.type==="managed-switch-card")||D.customCards.push({type:"managed-switch-card",name:"Managed Switch",description:"The front panel of a managed switch: ports by link and speed, PoE, connected devices.",preview:!0,documentationURL:"https://ha-managed-switch.eize.dev/card/"});console.info("%c MANAGED-SWITCH-CARD %c 0.6.0 ","color:#fff;background:#4078f2","");export{rt as ManagedSwitchCard,at as ManagedSwitchCardEditor};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
