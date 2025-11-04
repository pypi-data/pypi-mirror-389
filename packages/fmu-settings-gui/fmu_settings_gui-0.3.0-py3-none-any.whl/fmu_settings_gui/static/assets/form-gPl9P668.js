import{e as b,r as x,j as e,y as B}from"./index-Dastpg3d.js";import{l as E,c as f,T,f as F,a as h,S,G as D,C as y,m as R}from"./validator-CFS8HeGh.js";const V=b.div`
  form > div {
    margin-bottom: 1em;
  }

  button + button {
    margin-left: 8px;
  }
`,k=b.div`
  display: flex;
  gap: 8px;
`,{useAppForm:G}=f({fieldContext:F,formContext:h,fieldComponents:{TextField:T},formComponents:{CancelButton:y,GeneralButton:D,SubmitButton:S}});function I({name:a,label:r,value:i,placeholder:l,helperText:n,length:o,minLength:d,mutationCallback:j,mutationIsPending:C}){const[p,u]=x.useState(!0),[v,g]=x.useState(!0),c=E({length:o,minLength:d}),A=({message:t,formReset:m})=>{B.info(t),m(),u(!0)},s=G({defaultValues:{[a]:i},onSubmit:({formApi:t,value:m})=>{j({formValue:m,formSubmitCallback:A,formReset:t.reset})}});return e.jsx(V,{children:e.jsxs("form",{onSubmit:t=>{t.preventDefault(),t.stopPropagation(),s.handleSubmit()},children:[e.jsx(s.AppField,{name:a,...c&&{validators:{onBlur:c}},children:t=>e.jsx(t.TextField,{label:r,placeholder:l,helperText:n,isReadOnly:p,setSubmitDisabled:g})}),e.jsx(s.AppForm,{children:p?e.jsx(s.GeneralButton,{label:"Edit",onClick:()=>{u(!1)}}):e.jsxs(e.Fragment,{children:[e.jsx(s.SubmitButton,{label:"Save",disabled:v,isPending:C,helperTextDisabled:"Value can be submitted when it has been changed and is valid"}),e.jsx(s.CancelButton,{onClick:t=>{t.preventDefault(),s.reset(),u(!0)}})]})})]})})}const{useAppForm:P}=f({fieldContext:F,formContext:h,fieldComponents:{SearchField:R},formComponents:{SubmitButton:S}});function O({name:a,value:r,helperText:i,setStateCallback:l}){const n=P({defaultValues:{[a]:r},onSubmit:({formApi:o,value:d})=>{l(d[a]),o.reset()}});return e.jsx("form",{onSubmit:o=>{o.preventDefault(),o.stopPropagation(),n.handleSubmit()},children:e.jsxs(k,{children:[e.jsx(n.AppField,{name:a,children:o=>e.jsx(o.SearchField,{helperText:i,toUpperCase:!0})}),e.jsx(n.AppForm,{children:e.jsx(n.SubmitButton,{label:"Search"})})]})})}export{I as E,O as S};
