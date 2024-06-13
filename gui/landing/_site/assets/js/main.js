const menuToggler = () => {
  const toggle = document.querySelector('.page-header-menu__toggle')

  if (!toggle) {
    return
  }

  toggle.onclick = (e) => {
    const el = e.target.closest('.page-header-menu')
    el?.classList.toggle('show')
    document.documentElement.classList[[...el?.classList].includes('show') ? 'add' : 'remove'](
      'open-menu'
    )
  }

  window.addEventListener('click', (e) => {
    if (e.target.closest('.page-header-links__link')) {
      e.target.closest('.page-header-menu')?.classList.remove('show')
    }
  })
}

window.addEventListener("load", () => {
  menuToggler();

  const addTokenToMetmaskId = document.getElementById('addTokenToMetmaskId')
  if(addTokenToMetmaskId){
    addTokenToMetmaskId.onclick = addTokenToMetmask;
  }
});


const addTokenToMetmask = async () => {
  const options = {
    address: "0x525574C899A7c877a11865339e57376092168258",
    symbol: "GURU",
    decimals: 18,
    image: "https://assets.coingecko.com/coins/images/38583/standard/tGURU_token_circle.png"
  }
  
  try {
    const wasAdded = await window.ethereum
      .request({
        method: "wallet_watchAsset",
        params: {
          type: "ERC20",
          options
        },
      });
  
    if (wasAdded) {
      console.log("Thanks for your interest!");
    } else {
      console.log("Your loss!");
    }
  } catch (error) {
    console.log(error);
  }
}




